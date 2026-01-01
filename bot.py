import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import arabic_reshaper
from bidi.algorithm import get_display

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("8419911130:AAEi_iQLPovcJtykWbwy10IciLus4-eRmes")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# A4 – 300 DPI
PAGE_W, PAGE_H = 2480, 3508

# هوامش جامعية رسمية
MARGIN_RIGHT = 300
MARGIN_LEFT = 250
MARGIN_TOP = 350
MARGIN_BOTTOM = 300

LINE_SPACING = 60
FONT_SIZE = 42
HEADER_FONT_SIZE = 36
FOOTER_FONT_SIZE = 34

# ================== FONT ==================
def load_font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

FONT = load_font(FONT_SIZE)
HEADER_FONT = load_font(HEADER_FONT_SIZE)
FOOTER_FONT = load_font(FOOTER_FONT_SIZE)

# ================== ARABIC ==================
def ar(text):
    return get_display(arabic_reshaper.reshape(text))

# ================== PAGE TEMPLATE ==================
def create_page(page_number, meta):
    img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(img)

    # ===== HEADER =====
    header_text = f"{meta['university']} – {meta['college']} – {meta['department']}"
    title_text = meta["title"]

    draw.text(
        (PAGE_W // 2, 120),
        ar(header_text),
        font=HEADER_FONT,
        fill=(0, 0, 0),
        anchor="ma"
    )

    draw.text(
        (PAGE_W // 2, 180),
        ar(title_text),
        font=HEADER_FONT,
        fill=(0, 0, 0),
        anchor="ma"
    )

    # خط فاصل
    draw.line((200, 230, PAGE_W - 200, 230), fill=(0, 0, 0), width=2)

    # ===== FOOTER =====
    draw.text(
        (PAGE_W // 2, PAGE_H - 150),
        ar(f"{page_number}"),
        font=FOOTER_FONT,
        fill=(0, 0, 0),
        anchor="ma"
    )

    return img, draw

# ================== CONTENT ==================
def generate_research_text(title, pages):
    section = f"""
مقدمة:
يهدف هذا البحث إلى دراسة موضوع ({title}) دراسة علمية أكاديمية وفق المنهج العلمي المعتمد في البحوث الجامعية.

مشكلة البحث:
تتمحور مشكلة البحث حول تحليل أبعاد موضوع ({title}) بشكل منهجي.

أهمية البحث:
تكمن أهمية البحث في كونه يعالج موضوعاً معاصراً له قيمة علمية.

أهداف البحث:
1- توضيح المفاهيم الأساسية
2- تحليل الإطار النظري
3- تقديم نتائج وتوصيات

الإطار النظري:
يتناول هذا الفصل المفاهيم والنظريات المرتبطة بموضوع البحث.

الدراسات السابقة:
استعراض الدراسات السابقة ذات العلاقة.

المنهجية:
اعتمد البحث المنهج الوصفي التحليلي.

الخاتمة:
توصل البحث إلى نتائج مهمة مع توصيات مستقبلية.
"""
    return (section.strip() + "\n\n") * pages

# ================== LAYOUT ENGINE ==================
def build_pages(text, meta):
    words = text.split()
    max_width = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT
    lines, line = [], ""

    for w in words:
        test = (line + " " + w).strip()
        if FONT.getlength(ar(test)) <= max_width:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)

    pages = []
    page_num = 1
    img, draw = create_page(page_num, meta)
    y = MARGIN_TOP

    for l in lines:
        if y + LINE_SPACING > PAGE_H - MARGIN_BOTTOM:
            pages.append(img.copy())
            page_num += 1
            img, draw = create_page(page_num, meta)
            y = MARGIN_TOP

        draw.text(
            (PAGE_W - MARGIN_RIGHT, y),
            ar(l),
            font=FONT,
            fill=(0, 0, 0),
            anchor="ra"
        )
        y += LINE_SPACING

    pages.append(img.copy())
    return pages

# ================== PDF ==================
def images_to_pdf(images, path):
    c = canvas.Canvas(path, pagesize=A4)
    for img in images:
        temp = os.path.join(OUTPUT_DIR, "page.jpg")
        img.save(temp, "JPEG", quality=95)
        c.drawImage(temp, 0, 0, width=A4[0], height=A4[1])
        c.showPage()
    c.save()

# ================== BOT ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 بوت بحوث التخرج\n\n"
        "أرسل عنوان البحث فقط.\n"
        "سيتم إنشاء بحث جاهز مع:\n"
        "• رأس جامعة\n"
        "• تنسيق رسمي\n"
        "• ترقيم صفحات"
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    await update.message.reply_text("⏳ جاري إنشاء البحث بالتنسيق الجامعي الرسمي...")

    meta = {
        "university": "جامعة __________",
        "college": "كلية __________",
        "department": "قسم __________",
        "title": title
    }

    text = generate_research_text(title, pages=5)
    pages = build_pages(text, meta)

    pdf_path = os.path.join(OUTPUT_DIR, f"{title[:20]}.pdf")
    images_to_pdf(pages, pdf_path)

    await update.message.reply_document(
        document=open(pdf_path, "rb"),
        caption="✅ بحث تخرج رسمي مع ترقيم صفحات"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
