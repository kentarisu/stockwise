from flask import Flask, request, jsonify
import win32print

app = Flask(__name__)

def print_text(printer_name: str, content: str) -> None:
    hPrinter = win32print.OpenPrinter(printer_name)
    try:
        job_info = ("Sales Receipt", None, "RAW")
        win32print.StartDocPrinter(hPrinter, 1, job_info)
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, content.encode("utf-8"))
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)

@app.post("/print")
def do_print():
    data = request.get_json(force=True, silent=True) or {}
    content = data.get("content", "")
    printer_name = data.get("printer_name") or "POS58 Printer"
    if not content.strip():
        return jsonify(success=False, message="Empty content"), 400
    try:
        print_text(printer_name, content)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9100)

