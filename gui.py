#!/usr/bin/env python3
"""
GUI front-end for overlay_pdf.py
"""

import threading
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox

import fitz  # PyMuPDF – needed to read overlay page count

from overlay_pdf import determine_output_path, overlay_pdfs, validate_inputs

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


# ── helpers ──────────────────────────────────────────────────────────────────

def _pick_pdf(title, entry_var):
    path = filedialog.askopenfilename(
        title=title,
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
    )
    if path:
        entry_var.set(path)


def _pick_output(entry_var):
    path = filedialog.asksaveasfilename(
        title="Save output PDF as",
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
    )
    if path:
        entry_var.set(path)


def _get_overlay_page_count(path_str):
    try:
        doc = fitz.open(path_str)
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return None


# ── main window ───────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Overlayer")
        self.resizable(False, False)
        self._page_max = 0
        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        pad = dict(padx=10, pady=6)

        frame = ctk.CTkFrame(self)
        frame.grid(padx=12, pady=12, sticky="nsew")

        # Source PDF
        ctk.CTkLabel(frame, text="Source PDF:").grid(row=0, column=0, sticky="w", **pad)
        self.source_var = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.source_var, width=380).grid(row=0, column=1, **pad)
        ctk.CTkButton(frame, text="Browse…", width=80,
                      command=lambda: _pick_pdf("Select source PDF", self.source_var)
                      ).grid(row=0, column=2, **pad)

        # Overlays PDF
        ctk.CTkLabel(frame, text="Overlays PDF:").grid(row=1, column=0, sticky="w", **pad)
        self.overlays_var = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.overlays_var, width=380).grid(row=1, column=1, **pad)
        self.overlays_var.trace_add("write", self._on_overlays_changed)
        ctk.CTkButton(frame, text="Browse…", width=80,
                      command=lambda: [_pick_pdf("Select overlays PDF", self.overlays_var)]
                      ).grid(row=1, column=2, **pad)

        # Overlay page selector (spinner replacement)
        ctk.CTkLabel(frame, text="Overlay page:").grid(row=2, column=0, sticky="w", **pad)
        page_frame = ctk.CTkFrame(frame, fg_color="transparent")
        page_frame.grid(row=2, column=1, sticky="w", **pad)
        self.page_var = ctk.IntVar(value=0)
        ctk.CTkButton(page_frame, text="−", width=30,
                      command=self._decrement_page).grid(row=0, column=0, padx=(0, 4))
        self.page_entry = ctk.CTkEntry(page_frame, textvariable=self.page_var, width=50,
                                       justify="center")
        self.page_entry.grid(row=0, column=1)
        ctk.CTkButton(page_frame, text="+", width=30,
                      command=self._increment_page).grid(row=0, column=2, padx=(4, 0))
        self.page_count_label = ctk.CTkLabel(page_frame, text="  (open an overlays PDF first)",
                                             text_color="gray")
        self.page_count_label.grid(row=0, column=3, padx=(6, 0))

        # Output PDF
        ctk.CTkLabel(frame, text="Output PDF:").grid(row=3, column=0, sticky="w", **pad)
        self.output_var = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.output_var, width=380).grid(row=3, column=1, **pad)
        ctk.CTkButton(frame, text="Browse…", width=80,
                      command=lambda: _pick_output(self.output_var)
                      ).grid(row=3, column=2, **pad)
        ctk.CTkLabel(frame, text="(leave blank for auto)", text_color="gray"
                     ).grid(row=4, column=1, sticky="w", padx=10, pady=(0, 4))

        # Run button
        self.run_btn = ctk.CTkButton(frame, text="Run", command=self._run)
        self.run_btn.grid(row=5, column=0, columnspan=3, pady=(4, 8))

        # Log
        ctk.CTkLabel(frame, text="Log:").grid(row=6, column=0, sticky="nw", **pad)
        self.log = ctk.CTkTextbox(frame, width=480, height=160, state="disabled",
                                  wrap="word", font=("Courier", 11))
        self.log.grid(row=6, column=1, columnspan=2, **pad)

    # ── page spinner helpers ──────────────────────────────────────────────────

    def _decrement_page(self):
        v = self.page_var.get()
        if v > 0:
            self.page_var.set(v - 1)

    def _increment_page(self):
        v = self.page_var.get()
        if v < self._page_max:
            self.page_var.set(v + 1)

    # ── event handlers ───────────────────────────────────────────────────────

    def _on_overlays_changed(self, *_):
        path_str = self.overlays_var.get().strip()
        n = _get_overlay_page_count(path_str) if path_str else None
        if n is not None:
            self._page_max = n - 1
            self.page_count_label.configure(
                text=f"  (0 – {n - 1}, {n} page{'s' if n != 1 else ''})",
            )
            if self.page_var.get() >= n:
                self.page_var.set(0)
        else:
            self._page_max = 0
            self.page_count_label.configure(text="  (open an overlays PDF first)")

    def _run(self):
        source_str = self.source_var.get().strip()
        overlays_str = self.overlays_var.get().strip()
        output_str = self.output_var.get().strip()
        page_num = self.page_var.get()

        if not source_str or not overlays_str:
            messagebox.showerror("Missing input", "Please select both source and overlays PDFs.")
            return

        source_path = Path(source_str)
        overlays_path = Path(overlays_str)
        output_path = Path(output_str) if output_str else determine_output_path(source_path, None)

        self.run_btn.configure(state="disabled")
        self._log_clear()
        self._log(f"Source:   {source_path}")
        self._log(f"Overlays: {overlays_path} (page {page_num})")
        self._log(f"Output:   {output_path}")
        self._log("Running…")

        threading.Thread(
            target=self._worker,
            args=(source_path, overlays_path, output_path, page_num),
            daemon=True,
        ).start()

    def _worker(self, source_path, overlays_path, output_path, page_num):
        # Reuse CLI validation via a small namespace shim
        class Args:
            pass
        args = Args()
        args.source_pdf = source_path
        args.overlays_pdf = overlays_path
        args.overlay_page = page_num

        # Capture stderr-style errors by wrapping validate_inputs
        import io, contextlib
        buf = io.StringIO()
        try:
            with contextlib.redirect_stderr(buf):
                validate_inputs(args)
        except SystemExit:
            self.after(0, self._log, buf.getvalue().strip())
            self.after(0, self._finish, False)
            return

        rc = overlay_pdfs(source_path, overlays_path, output_path, page_num, verbose=True)
        if rc == 0:
            self.after(0, self._log, f"Done! Saved to: {output_path}")
            self.after(0, self._finish, True)
        else:
            self.after(0, self._log, "Failed — see log above.")
            self.after(0, self._finish, False)

    def _finish(self, success):
        self.run_btn.configure(state="normal")
        if success:
            messagebox.showinfo("Done", f"PDF created successfully.")

    # ── log helpers ──────────────────────────────────────────────────────────

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _log_clear(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
