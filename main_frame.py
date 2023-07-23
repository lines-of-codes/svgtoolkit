import io
import os
import tkinter as tk
from threading import Thread
from tkinter import (
    BOTH,
    BOTTOM,
    LEFT,
    RIGHT,
    TOP,
    Frame,
    X,
    Y,
    filedialog,
    messagebox,
    ttk,
)

from PIL import Image, ImageTk
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg


class Progress(Frame):
    def __init__(self, master, text, maxval=100):
        super().__init__(master)

        self.worker_label = ttk.Label(self, text=text)
        self.worker_label.pack()

        self.progress_bar = ttk.Progressbar(self, mode="determinate", maximum=maxval)
        self.progress_bar.pack()

    def set_progress(self, number):
        self.progress_bar.configure(value=number)


class MainFrame(Frame):
    def __init__(self, master, files=[]):
        super().__init__(master)

        self.files = files
        self.items = {}

        self.not_image = "not image"

        self.init_ui()

    def update_preview(self, event):
        selections = self.file_tree.selection()
        if len(selections) == 1:
            file = self.items[selections[0]]

            if file == self.not_image:
                return

            self.fileName.configure(text=file)

            photoData = io.BytesIO()
            renderPM.drawToFile(svg2rlg(file), photoData, "PNG")

            self.selectedImage = ImageTk.PhotoImage(file=photoData)
            if self.image_preview is not None:
                self.image_preview.configure(image=self.selectedImage)
            else:
                self.image_preview = ttk.Label(
                    self.preview_frame, image=self.selected_image
                )
                self.image_preview.pack()
            return
        elif len(selections) > 1:
            self.fileName.configure(text="Multiple file selected.")

        if self.image_preview is not None:
            self.image_preview.pack()

    def add_file_to_tree(self, file, parent):
        photoData = io.BytesIO()
        renderPM.drawToFile(svg2rlg(file), photoData, "PNG")

        self.items[
            self.file_tree.insert(
                parent,
                "end",
                text=os.path.basename(file),
                image=ImageTk.PhotoImage(file=photoData),
            )
        ] = file

    def add_files_to_tree(self, files, parent):
        for file in files:
            self.add_file_to_tree(file, parent)

    def add_file(self):
        self.add_files_to_tree(
            filedialog.askopenfilenames(
                filetypes=[("Scalable Vector Graphics", "*.svg")]
            ),
            self.treeRoot,
        )

    def ask_add_folder(self):
        directory = filedialog.askdirectory()

        if not directory:
            return

        self.importing_state_dialog = tk.Toplevel()
        self.importing_state_dialog.grab_set()
        self.import_status = ttk.Label(self.importing_state_dialog, text="Importing...")
        self.import_status.pack()

        self.import_close_btn = ttk.Button(
            self.importing_state_dialog,
            text="Completed!",
            command=self.importing_state_dialog.destroy,
        )

        Thread(target=lambda: self.add_folder(directory, self.treeRoot)).run()

    def add_folder(self, directory, parent, is_target=True):
        paths = {}

        target_dir_name = os.path.basename(directory)
        target_dir = self.file_tree.insert(parent, "end", text=target_dir_name)
        self.items[target_dir] = self.not_image

        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            print(f"Importing: {full_path}")
            if os.path.isdir(full_path):
                self.add_folder(full_path, target_dir, is_target=False)
                continue
            if os.path.isfile(full_path) and entry.endswith(".svg"):
                self.add_file_to_tree(full_path, target_dir)

        if is_target:
            self.import_close_btn.pack()
        print(f"Import finished for directory {directory}")

    def export_png(self):
        selections = self.file_tree.selection()

        needed_export = 0
        export_list = []

        for selection in selections:
            if self.items[selection] == self.not_image:
                continue
            needed_export += 1
            export_list.append(self.items[selection])

        if needed_export == 0:
            messagebox.showerror(
                "No file selected",
                "No files selected. Please select a file before exporting. Selected folders are ignored.",
            )
            return

        if needed_export == 1:
            target_file = filedialog.asksaveasfilename(
                filetypes=[("Portable Network Graphics", "*.png")],
                initialfile=os.path.basename(export_list[0]).removesuffix(".svg")
                + ".png",
            )

            if not target_file:
                return

            renderPM.drawToFile(svg2rlg(export_list[0]), target_file, "PNG")
            messagebox.showinfo("Export complete", "An export of 1 image is completed.")
            return

        output_directory = filedialog.askdirectory(title="Select output folder...")

        if not output_directory:
            return

        if len(os.listdir(output_directory)) != 0:
            messagebox.showerror(
                "Folder not empty.",
                "Please select an empty folder to avoid file name conflict.",
            )
            return

        progress_dialog = tk.Toplevel()
        export_progress = Progress(
            progress_dialog, "Exporting...", maxval=needed_export
        )
        export_progress.pack()
        exported_count = 0

        for file in export_list:
            file_name = os.path.basename(file).removesuffix(".svg") + ".png"
            full_path = os.path.join(
                output_directory,
                file_name,
            )
            text = f"Exporting: {full_path}"
            export_progress.worker_label.configure(text=text)
            print(text)
            renderPM.drawToFile(
                svg2rlg(file),
                full_path,
                "PNG",
            )
            exported_count += 1
            export_progress.set_progress(exported_count)

        export_progress.worker_label.configure(text="Export complete!")
        ttk.Button(
            progress_dialog, text="Close", command=progress_dialog.destroy
        ).pack()

    def select_all_images(self):
        select_target = []

        for key, value in self.items.items():
            if value != self.not_image:
                select_target.append(key)

        self.file_tree.selection_set(select_target)
    
    def remove_items(self):
        selections = self.file_tree.selection()
        self.file_tree.delete(*selections)
        for selection in selections:
            del self.items[selection]

    def init_ui(self):
        left_side = ttk.Frame(self)

        self.file_tree = ttk.Treeview(left_side)
        self.file_tree.bind("<<TreeviewSelect>>", self.update_preview)
        self.treeRoot = self.file_tree.insert("", "end", text="Assets")
        self.items[self.treeRoot] = self.not_image

        self.add_files_to_tree(self.files, self.treeRoot)

        self.file_tree.pack(fill=BOTH, padx=10, pady=10, ipady=50)

        buttons = ttk.Frame(left_side)

        ttk.Button(buttons, text="Export PNG", command=self.export_png).pack(fill=X)
        ttk.Button(buttons, text="Add file", command=self.add_file).pack(fill=X)
        ttk.Button(buttons, text="Add folder", command=self.ask_add_folder).pack(fill=X)
        ttk.Button(
            buttons, text="Select all images", command=self.select_all_images
        ).pack(fill=X)
        ttk.Button(
            buttons, text="Remove item from list", command=self.remove_items
        ).pack(fill=X)

        buttons.pack(fill=X, padx=10, pady=10)
        left_side.pack(side=LEFT, fill=BOTH, ipadx=50)

        self.preview_frame = ttk.Frame(self)
        self.fileName = ttk.Label(self.preview_frame)
        self.fileName.pack()
        self.selected_image = None
        self.image_preview = None
        self.preview_frame.pack(side=RIGHT, fill=Y, padx=10, pady=10)
