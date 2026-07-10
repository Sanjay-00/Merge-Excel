import io

import pandas as pd


def to_excel_bytes(df, progress_cb=None):
    import xlsxwriter

    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {"constant_memory": True})
    ws = wb.add_worksheet("Merged")

    for ci, col in enumerate(df.columns):
        ws.write(0, ci, col)

    total = len(df)
    chunk = 5000
    for start in range(0, total, chunk):
        end = min(start + chunk, total)
        for ri, row in enumerate(df.iloc[start:end].values.tolist()):
            for ci, val in enumerate(row):
                if pd.notna(val):
                    ws.write(start + ri + 1, ci, val)
        if progress_cb:
            progress_cb(end, total)

    wb.close()
    return buf.getvalue()
