import json
import os
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from escpos.printer import Serial, Network, File


def _wrap(s, width):
    s = (s or "").strip()
    out, line = [], ""
    for w in s.split():
        if len(line) + len(w) + (1 if line else 0) <= width:
            line = (line + (" " if line else "") + w)
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def connect_printer(connection_type, params):
    if connection_type == "serial" or connection_type == "bluetooth":
        port = params.get("port")
        baudrate = int(params.get("baudrate") or 9600)
        p = Serial(devfile=port, baudrate=baudrate, bytesize=8, timeout=1, dsrdtr=True)
        return p, None, None
    if connection_type == "network":
        host = params.get("host")
        port = int(params.get("port") or 9100)
        p = Network(host=host, port=port, timeout=3)
        return p, None, None
    if connection_type == "windows":
        name = params.get("printer_name") or "POS58 Printer"
        tmp = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".prn")
        path = tmp.name
        tmp.close()
        p = File(devfile=path)
        return p, path, name
    raise ValueError("unsupported connection type")


def send_windows_job(path, printer_name):
    try:
        import win32print
        import win32con
        with open(path, "rb") as f:
            data = f.read()
        h = win32print.OpenPrinter(printer_name)
        try:
            job = win32print.StartDocPrinter(h, 1, ("StockWise", None, "RAW"))
            win32print.StartPagePrinter(h)
            win32print.WritePrinter(h, data)
            win32print.EndPagePrinter(h)
            win32print.EndDocPrinter(h)
        finally:
            win32print.ClosePrinter(h)
        try:
            os.unlink(path)
        except Exception:
            pass
        return True
    except Exception:
        return False


def print_receipt(p, receipt):
    company = (receipt.get("company_name") or "StockWise").strip()
    addr = (receipt.get("company_address") or "").strip()
    phone = (receipt.get("company_phone") or "").strip()
    p.set(align="center", bold=True, double_height=True)
    p.text(company + "\n")
    p.set(align="center", bold=False, double_height=False)
    for line in _wrap(addr, 32):
        p.text(line + "\n")
    if phone:
        p.text("Tel: " + phone + "\n")
    p.text("\n")
    p.set(align="center", bold=True)
    p.text("SALES RECEIPT\n\n")
    p.set(align="left", bold=False)
    p.text("Transaction No.: " + str(receipt.get("transaction_number") or "N/A") + "\n")
    p.text("OR No.: " + str(receipt.get("or_number") or "N/A") + "\n")
    p.text("Date: " + str(receipt.get("date") or "N/A") + "\n")
    if receipt.get("processed_by"):
        p.text("Processed by: " + str(receipt.get("processed_by")) + "\n")
    p.text("-" * 32 + "\n")
    cust = (receipt.get("customer_name") or "").strip()
    if cust and cust != "N/A":
        p.text("Customer: " + cust + "\n")
    contact = (receipt.get("customer_contact") or "").strip()
    if contact:
        p.text("Contact: " + contact + "\n")
    caddr = (receipt.get("customer_address") or "").strip()
    if caddr and caddr != "N/A":
        lines = _wrap(caddr, 32)
        for i, line in enumerate(lines):
            p.text(("Address: " if i == 0 else "          ") + line + "\n")
    p.text("-" * 32 + "\n")
    items = receipt.get("items") or []
    if items:
        p.set(bold=True)
        p.text("Description           Qty     Amount\n")
        p.set(bold=False)
        for it in items:
            name = (it.get("name") or "Item").strip()
            qty = int(it.get("quantity") or it.get("qty") or 0)
            amount = float(it.get("amount") or it.get("price") or 0)
            first = _wrap(name, 18)[0]
            line = f"{first:<18}{qty:>4}{amount:>10.2f}"
            p.text(line + "\n")
            extras = _wrap(name, 32)[1:]
            for e in extras:
                p.text(e + "\n")
    p.text("-" * 32 + "\n")
    subtotal = float(receipt.get("subtotal") or 0)
    vat = float(receipt.get("vat") or 0)
    total = float(receipt.get("total") or 0)
    paid = float(receipt.get("amount_paid") or 0)
    change = float(receipt.get("change") or 0)
    discount = float(receipt.get("discount") or 0)
    pct = float(receipt.get("discount_pct") or 0)
    p.text(f"Subtotal: {subtotal:,.2f}\n")
    if vat > 0:
        p.text(f"VAT 12%: {vat:,.2f}\n")
    if discount > 0:
        sfx = (f" ({pct:g}%)" if pct > 0 else "")
        p.text(f"Discount{sfx}: -{discount:,.2f}\n")
    p.set(bold=True, double_height=True)
    p.text(f"TOTAL: {total:,.2f}\n")
    p.set(bold=False, double_height=False)
    p.text(f"Amount Paid: {paid:,.2f}\n")
    p.text(f"Change: {change:,.2f}\n")
    p.text("-" * 32 + "\n")
    p.set(align="center")
    p.text("Thank you for your purchase!\n")
    p.text("This is not an official receipt.\n")
    p.cut()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            data = self.rfile.read(length).decode("utf-8")
            payload = json.loads(data or "{}")
            action = payload.get("action")
            connection_type = payload.get("connection_type") or "serial"
            params = payload.get("params") or {}
            printer, temp_path, printer_name = connect_printer(connection_type, params)
            try:
                if action == "test_print":
                    printer.text("StockWise Test\n")
                    printer.text("Test print\n")
                    printer.cut()
                elif action == "print_receipt":
                    receipt = payload.get("receipt") or {}
                    print_receipt(printer, receipt)
                else:
                    raise ValueError("invalid action")
            finally:
                try:
                    printer.close()
                except Exception:
                    pass
            ok = True
            if connection_type == "windows" and temp_path:
                ok = send_windows_job(temp_path, printer_name)
            body = json.dumps({"success": bool(ok)}).encode("utf-8")
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body = json.dumps({"success": False, "error": str(e)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def run():
    host = os.getenv("BRIDGE_HOST", "0.0.0.0")
    port = int(os.getenv("BRIDGE_PORT", "8008"))
    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
