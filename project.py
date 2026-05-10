import flet as ft
import pandas as pd
import os
from datetime import datetime

def main(page: ft.Page):
    # تنظیمات اولیه صفحه
    page.title = "مغایرت‌گیری بانکی"
    page.window_width = 450
    page.window_height = 800
    page.window_min_width = 360
    page.window_min_height = 600
    page.rtl = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    # متغیرهای ذخیره داده
    bank_df = None
    book_df = None
    bank_path = ""
    book_path = ""

    # ویجت‌های وضعیت
    bank_status = ft.Text("📂 هیچ فایلی انتخاب نشده", size=14, color=ft.colors.GREY_700)
    book_status = ft.Text("📂 هیچ فایلی انتخاب نشده", size=14, color=ft.colors.GREY_700)
    progress = ft.ProgressRing(visible=False, width=30, height=30)
    result_text = ft.Text("", selectable=True, size=14, text_align=ft.TextAlign.CENTER)

    # جداول نمایش نتایج (با اسکرول عمودی و افقی)
    bank_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ردیف", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("تاریخ", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("شرح", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("بدهکار", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("بستانکار", weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        heading_row_color=ft.colors.GREY_100,
        column_spacing=20,
        data_row_min_height=40,
        width=page.window_width - 40,
    )
    book_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ردیف", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("تاریخ", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("شرح", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("بدهکار", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("بستانکار", weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        heading_row_color=ft.colors.GREY_100,
        column_spacing=20,
        data_row_min_height=40,
        width=page.window_width - 40,
    )

    # FilePicker ها
    bank_file_picker = ft.FilePicker(on_result=lambda e: on_bank_file_selected(e))
    book_file_picker = ft.FilePicker(on_result=lambda e: on_book_file_selected(e))
    page.overlay.append(bank_file_picker)
    page.overlay.append(book_file_picker)

    # توابع انتخاب فایل
    def on_bank_file_selected(e: ft.FilePickerResultEvent):
        nonlocal bank_df, bank_path
        if e.files:
            file = e.files[0]
            bank_path = file.path
            try:
                # خواندن فایل اکسل
                df = pd.read_excel(bank_path, header=0)
                if df.shape[1] < 4:
                    raise ValueError("فایل باید حداقل 4 ستون داشته باشد")
                # استانداردسازی نام ستون‌ها
                df.columns = ["تاریخ", "شرح", "بدهکار", "بستانکار"] + list(df.columns[4:])[:df.shape[1]-4]
                df["بدهکار"] = pd.to_numeric(df["بدهکار"], errors="coerce").fillna(0)
                df["بستانکار"] = pd.to_numeric(df["بستانکار"], errors="coerce").fillna(0)
                bank_df = df
                bank_status.value = f"✅ {file.name} | {len(df)} ردیف"
                bank_status.color = ft.colors.GREEN
            except Exception as ex:
                bank_status.value = f"❌ خطا: {str(ex)[:50]}"
                bank_status.color = ft.colors.RED
                bank_df = None
            page.update()

    def on_book_file_selected(e: ft.FilePickerResultEvent):
        nonlocal book_df, book_path
        if e.files:
            file = e.files[0]
            book_path = file.path
            try:
                df = pd.read_excel(book_path, header=0)
                if df.shape[1] < 4:
                    raise ValueError("فایل باید حداقل 4 ستون داشته باشد")
                df.columns = ["تاریخ", "شرح", "بدهکار", "بستانکار"] + list(df.columns[4:])[:df.shape[1]-4]
                df["بدهکار"] = pd.to_numeric(df["بدهکار"], errors="coerce").fillna(0)
                df["بستانکار"] = pd.to_numeric(df["بستانکار"], errors="coerce").fillna(0)
                book_df = df
                book_status.value = f"✅ {file.name} | {len(df)} ردیف"
                book_status.color = ft.colors.GREEN
            except Exception as ex:
                book_status.value = f"❌ خطا: {str(ex)[:50]}"
                book_status.color = ft.colors.RED
                book_df = None
            page.update()

    # تابع مغایرت‌گیری
    def run_reconciliation(e):
        if bank_df is None or book_df is None:
            page.snack_bar = ft.SnackBar(ft.Text("لطفاً هر دو فایل را انتخاب کنید"), open=True)
            page.update()
            return

        progress.visible = True
        page.update()

        try:
            # کپی از دیتافریم‌ها
            b = bank_df.copy()
            d = book_df.copy()

            # ایجاد کلید ترکیبی (تاریخ + بدهکار + بستانکار)
            b["date_key"] = pd.to_datetime(b["تاریخ"], errors="coerce").dt.strftime("%Y%m%d")
            d["date_key"] = pd.to_datetime(d["تاریخ"], errors="coerce").dt.strftime("%Y%m%d")
            b["key"] = b["date_key"] + "_" + b["بدهکار"].astype(str) + "_" + b["بستانکار"].astype(str)
            d["key"] = d["date_key"] + "_" + d["بدهکار"].astype(str) + "_" + d["بستانکار"].astype(str)

            # یافتن موارد مغایر
            only_bank = b[~b["key"].isin(d["key"])].copy()
            only_book = d[~d["key"].isin(b["key"])].copy()

            # پر کردن جدول بانک
            bank_table.rows.clear()
            for idx, row in only_bank.iterrows():
                bank_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(idx + 2))),
                        ft.DataCell(ft.Text(str(row["تاریخ"])[:12])),
                        ft.DataCell(ft.Text(str(row["شرح"])[:50])),
                        ft.DataCell(ft.Text(f"{row['بدهکار']:,.0f}")),
                        ft.DataCell(ft.Text(f"{row['بستانکار']:,.0f}")),
                    ])
                )

            # پر کردن جدول دفتر
            book_table.rows.clear()
            for idx, row in only_book.iterrows():
                book_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(idx + 2))),
                        ft.DataCell(ft.Text(str(row["تاریخ"])[:12])),
                        ft.DataCell(ft.Text(str(row["شرح"])[:50])),
                        ft.DataCell(ft.Text(f"{row['بدهکار']:,.0f}")),
                        ft.DataCell(ft.Text(f"{row['بستانکار']:,.0f}")),
                    ])
                )

            # محاسبات
            sum_bank_debit = only_bank["بدهکار"].sum()
            sum_bank_credit = only_bank["بستانکار"].sum()
            sum_book_debit = only_book["بدهکار"].sum()
            sum_book_credit = only_book["بستانکار"].sum()
            diff = (sum_bank_debit - sum_bank_credit) - (sum_book_debit - sum_book_credit)

            # نمایش نتیجه
            result = f"🔴 فقط در بانک: {len(only_bank)} قلم\n"
            result += f"🔵 فقط در دفتر: {len(only_book)} قلم\n"
            result += f"💰 خالص بانک: {(sum_bank_debit - sum_bank_credit):,.0f} ریال\n"
            result += f"📒 خالص دفتر: {(sum_book_debit - sum_book_credit):,.0f} ریال\n"
            result += f"⚖️ اختلاف نهایی: {diff:,.0f} ریال"
            if diff == 0:
                result += "\n✅ تطابق کامل است"
            else:
                result += "\n⚠️ مغایرت وجود دارد"
            result_text.value = result
            result_text.color = ft.colors.GREEN if diff == 0 else ft.colors.ORANGE

            # ذخیره برای گزارش
            page.only_bank = only_bank
            page.only_book = only_book
            save_button.visible = True
            page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"خطا: {str(ex)}"), open=True)
        finally:
            progress.visible = False
            page.update()

    # ذخیره گزارش به فایل اکسل
    def save_report(e):
        if hasattr(page, 'only_bank') and hasattr(page, 'only_book'):
            filename = f"moghayerat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            with pd.ExcelWriter(filename) as writer:
                page.only_bank.to_excel(writer, sheet_name="فقط_در_بانک", index=False)
                page.only_book.to_excel(writer, sheet_name="فقط_در_دفتر", index=False)
            page.snack_bar = ft.SnackBar(ft.Text(f"گزارش ذخیره شد: {filename}"), open=True)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("ابتدا مغایرت‌گیری را اجرا کنید"), open=True)
        page.update()

    # ریست کردن همه چیز
    def reset(e):
        nonlocal bank_df, book_df
        bank_df = None
        book_df = None
        bank_status.value = "📂 هیچ فایلی انتخاب نشده"
        bank_status.color = ft.colors.GREY_700
        book_status.value = "📂 هیچ فایلی انتخاب نشده"
        book_status.color = ft.colors.GREY_700
        result_text.value = ""
        bank_table.rows.clear()
        book_table.rows.clear()
        save_button.visible = False
        page.update()

    # دکمه‌ها (با طراحی واضح و قابل کلیک)
    bank_btn = ft.ElevatedButton(
        text="انتخاب فایل بانک",
        icon=ft.icons.ACCOUNT_BALANCE_WALLET,
        on_click=lambda _: bank_file_picker.pick_files(allow_multiple=False),
        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.BLUE, padding=15),
        expand=True,
    )
    book_btn = ft.ElevatedButton(
        text="انتخاب فایل دفتر کل",
        icon=ft.icons.BOOK,
        on_click=lambda _: book_file_picker.pick_files(allow_multiple=False),
        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREEN, padding=15),
        expand=True,
    )
    recon_btn = ft.ElevatedButton(
        text="شروع مغایرت‌گیری",
        icon=ft.icons.SEARCH,
        on_click=run_reconciliation,
        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.PURPLE, padding=15),
        expand=True,
    )
    save_button = ft.ElevatedButton(
        text="ذخیره گزارش اکسل",
        icon=ft.icons.SAVE,
        on_click=save_report,
        visible=False,
        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.TEAL, padding=15),
        expand=True,
    )
    reset_btn = ft.TextButton(
        text="ریست",
        icon=ft.icons.RESTART_ALT,
        on_click=reset,
        style=ft.ButtonStyle(color=ft.colors.RED),
    )

    # ساختار صفحه (استفاده از Column با اسکرول طبیعی)
    page.add(
        ft.Column(
            [
                ft.Container(
                    content=ft.Text("🧾 مغایرت‌گیری بانکی", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    margin=ft.margin.only(bottom=10),
                ),
                ft.Row([bank_btn], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([bank_status], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([book_btn], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([book_status], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([recon_btn, reset_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Divider(height=10),
                ft.ExpansionTile(
                    title=ft.Text("🔴 موارد فقط در بانک", weight=ft.FontWeight.BOLD),
                    collapsed_text_color=ft.colors.RED,
                    text_color=ft.colors.RED,
                    controls=[
                        ft.Container(
                            content=ft.Column([bank_table], scroll=ft.ScrollMode.AUTO, height=300),
                            padding=5,
                        )
                    ],
                ),
                ft.ExpansionTile(
                    title=ft.Text("🔵 موارد فقط در دفتر", weight=ft.FontWeight.BOLD),
                    collapsed_text_color=ft.colors.BLUE,
                    text_color=ft.colors.BLUE,
                    controls=[
                        ft.Container(
                            content=ft.Column([book_table], scroll=ft.ScrollMode.AUTO, height=300),
                            padding=5,
                        )
                    ],
                ),
                ft.Card(
                    content=ft.Container(result_text, padding=15),
                    elevation=3,
                    margin=ft.margin.only(top=10),
                ),
                ft.Row([save_button], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([progress], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
    )

# اجرای برنامه
ft.app(target=main)
