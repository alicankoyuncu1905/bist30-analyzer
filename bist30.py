mport yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
import pandas as pd
 
# Email configuration
EMAIL = ""
PASSWORD = ""  # Gmail App Password
RECIPIENT = ""
 
# All BIST30 companies
BIST30_TICKERS = {
    'AKBNK.IS': 'AKBNK',  # Akbank
    'ARCLK.IS': 'ARCLK',  # Arçelik
    'ASELS.IS': 'ASELS',  # Aselsan
    'BIMAS.IS': 'BIMAS',  # BIM Birleşik Mağazalar
    'DOHOL.IS': 'DOHOL',  # Doğan Holding
    'EKGYO.IS': 'EKGYO',  # Emlak Konut GYO
    'ENKAI.IS': 'ENKAI',  # Enka İnşaat
    'EREGL.IS': 'EREGL',  # Ereğli Demir Çelik
    'FROTO.IS': 'FROTO',  # Ford Otosan
    'GARAN.IS': 'GARAN',  # Garanti Bankası
    'GUBRF.IS': 'GUBRF',  # Gübre Fabrikaları
    'HALKB.IS': 'HALKB',  # Halkbank
    'ISCTR.IS': 'ISCTR',  # İş Bankası
    'KCHOL.IS': 'KCHOL',  # Koç Holding
    'KONTR.IS': 'KONTR',  # Kontrolmatik Teknoloji
    'KOZAA.IS': 'KOZAA',  # Koza Anadolu Metal
    'KOZAL.IS': 'KOZAL',  # Koza Altın
    'KRDMD.IS': 'KRDMD',  # Kardemir Karabük
    'MGROS.IS': 'MGROS',  # Migros Ticaret
    'ODAS.IS': 'ODAS',    # Odaş Elektrik
    'PETKM.IS': 'PETKM',  # Petkim
    'PGSUS.IS': 'PGSUS',  # Pegasus Hava Yolları
    'SAHOL.IS': 'SAHOL',  # Sabancı Holding
    'SASA.IS': 'SASA',    # Sasa Polyester
    'SISE.IS': 'SISE',    # Şişe Cam
    'TCELL.IS': 'TCELL',  # Turkcell
    'THYAO.IS': 'THYAO',  # Türk Hava Yolları
    'TOASO.IS': 'TOASO',  # Tofaş Oto
    'TUPRS.IS': 'TUPRS',  # Tüpraş
    'YKBNK.IS': 'YKBNK'   # Yapı Kredi Bankası
}
 
def generate_chart():
    """Generate chart with TRY prices only, return table data for last 7 days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
 
    # Fetch USDTRY exchange rate
    usd_try = yf.download('USDTRY=X', start=start_date, end=end_date)["Close"]
    if usd_try.empty:
        raise Exception("USDTRY data not found.")
   
    # Create figure with single y-axis
    fig, ax = plt.subplots(figsize=(14, 8))
    colors = plt.cm.tab10.colors * 3  # Repeat colors to cover 30 companies
 
    # Table data for the last 7 days
    table_data = pd.DataFrame(index=usd_try.index[-7:])  # Last 7 days
    table_data["USD/TRY"] = usd_try[-7:]
 
    # Plot stock prices in TRY on the single y-axis
    for i, (ticker, label) in enumerate(BIST30_TICKERS.items()):
        stock_close = yf.download(ticker, start=start_date, end=end_date)["Close"]
        if stock_close.empty:
            print(f"Warning: No data for {ticker}")
            table_data[label] = None
            continue
        ax.plot(stock_close.index, stock_close, color=colors[i], label=f"{label} (TRY)")
        # Add TRY prices to table
        table_data[label] = stock_close[-7:]
 
    # Customize axes
    latest_date = usd_try.dropna().index[-1].strftime('%Y-%m-%d')
    ax.set_title(f"BIST30 Companies in TRY (Last 6 Months, as of {latest_date})", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (TRY)", color='tab:blue')
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax.legend(loc='upper left', fontsize=9, ncol=3)  # 3 columns for 30 companies
    ax.grid(True, linestyle="--", alpha=0.7)
    plt.xticks(rotation=45)
 
    chart_path = "bist30_try_chart.png"
    plt.tight_layout()
    plt.savefig(chart_path, dpi=100)
    plt.close()
 
    # Calculate USD values for the table
    for label in BIST30_TICKERS.values():
        if label in table_data.columns and not table_data[label].isna().all():
            table_data[f"{label} (USD)"] = table_data[label] / table_data["USD/TRY"]
 
    return chart_path, table_data
 
def send_email():
    try:
        print("Creating chart...")
        chart_path, table_data = generate_chart()
        print("Chart saved:", chart_path)
 
        # Generate HTML table
        table_html = table_data.to_html(
            float_format="%.2f",  # 2 decimal places
            na_rep="N/A",         # Handle missing data
            index_names=True      # Show dates as index
        )
        table_html = f"""
        <style>
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: right;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
        {table_html}
        """
 
        msg = MIMEMultipart("related")
        msg["From"] = EMAIL
        msg["To"] = RECIPIENT
        msg["Subject"] = "BIST30 Companies in TRY with USD Conversion - Last 6 Months"
 
        html = f"""
        <html>
            <body>
                <h2>BIST30 Companies in TRY</h2>
                <p>This chart shows the stock prices of all 30 BIST30 companies in TRY over the last 6 months.</p>
                <p><b>Legend:</b><br>
                - AKBNK: Akbank<br>
                - ARCLK: Arçelik<br>
                - ASELS: Aselsan<br>
                - BIMAS: BİM Birleşik Mağazalar<br>
                - DOHOL: Doğan Holding<br>
                - EKGYO: Emlak Konut GYO<br>
                - ENKAI: Enka İnşaat<br>
                - EREGL: Ereğli Demir Çelik<br>
                - FROTO: Ford Otosan<br>
                - GARAN: Garanti Bankası<br>
                - GUBRF: Gübre Fabrikaları<br>
                - HALKB: Halkbank<br>
                - ISCTR: İş Bankası<br>
                - KCHOL: Koç Holding<br>
                - KONTR: Kontrolmatik Teknoloji<br>
                - KOZAA: Koza Anadolu Metal<br>
                - KOZAL: Koza Altın<br>
                - KRDMD: Kardemir Karabük<br>
                - MGROS: Migros Ticaret<br>
                - ODAS: Odaş Elektrik<br>
                - PETKM: Petkim<br>
                - PGSUS: Pegasus Hava Yolları<br>
                - SAHOL: Sabancı Holding<br>
                - SASA: Sasa Polyester<br>
                - SISE: Şişe Cam<br>
                - TCELL: Turkcell<br>
                - THYAO: Türk Hava Yolları<br>
                - TOASO: Tofaş Oto<br>
                - TUPRS: Tüpraş<br>
                - YKBNK: Yapı Kredi Bankası<br>
                </p>
                <img src="cid:chart_cid" alt="BIST30 TRY Chart"><br>
                <h3>Prices and USD Values (Last 7 Days)</h3>
                {table_html}
                <p>Stock prices in TRY shown in chart. Table includes TRY prices, USD/TRY rate, and calculated USD values for the last 7 days. Data from Yahoo Finance.</p>
            </body>
        </html>
        """
 
        alt = MIMEMultipart("alternative")
        msg.attach(alt)
        alt.attach(MIMEText(html, "html"))
 
        with open(chart_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<chart_cid>')
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(chart_path))
            msg.attach(img)
 
        print("Sending email...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.send_message(msg)
 
        print("✅ Email sent!")
        os.remove(chart_path)
 
    except Exception as e:
        print("❌ An error occurred:", e)
        import traceback
        traceback.print_exc()
 
# Run the script
if __name__ == "__main__":
    send_email()
