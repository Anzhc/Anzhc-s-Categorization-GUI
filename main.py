import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                               QPushButton, QWidget, QLabel, QLineEdit, QGridLayout,
                               QFileDialog, QSplitter, QSizePolicy, QFrame, QScrollArea,
                               QGroupBox, QMessageBox)
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QDateTime, QPropertyAnimation, QEasingCurve, Qt, QAbstractAnimation
import shutil
import random

class CategoryWidget(QWidget):
    assignImage = Signal()  # Define the custom signal here
    def __init__(self):
        super().__init__()
        self.original_pixmap = None

        self.layout = QVBoxLayout(self)
        self.frame = QFrame()
        self.frame.setStyleSheet("border: 2px solid black;")  # Style the frame
        self.frame_layout = QVBoxLayout(self.frame)
        self.image_preview = QLabel("Assign")
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setStyleSheet("font: bold; font-size: 16px;")
        self.category_name_input = QLineEdit()
        self.category_name_input.setStyleSheet("border: 1px solid black;")
        self.category_name_input.setPlaceholderText("Write category name here...")
        self.frame_layout.addWidget(self.image_preview)
        self.layout.addWidget(self.frame)
        self.layout.addWidget(self.category_name_input)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.frame.setStyleSheet("border: 2px solid blue;")  # Change border color on click
        self.assignImage.emit()  # Emit the custom signal when the widget is clicked

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.rescale_image_preview()

    def rescale_image_preview(self):
        if self.original_pixmap:
            self.image_preview.setPixmap(
                self.original_pixmap.scaled(self.frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def set_image_preview(self, pixmap):
        if not self.image_preview.pixmap():
            self.original_pixmap = pixmap  # Store the original pixmap
            self.image_preview.setPixmap(pixmap.scaled(self.frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.image_preview.setText("")  # Remove "Assign" text

    def update_width(self, width):
        adjusted_width = width - 20  # accounting for a 2-pixel border on each side
        self.setFixedWidth(adjusted_width)

    def get_category_name(self):
        return self.category_name_input.text()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.processed_images_count = 0

        self.categories_images = {}

        self.setMinimumSize(800, 600)

        # Main Layout
        self.main_layout = QVBoxLayout()

        # Button Line
        self.button_line = QWidget()
        self.button_layout = QHBoxLayout(self.button_line)
        self.open_folder_btn = QPushButton('Open Folder')
        self.save_btn = QPushButton('Save')
        self.button_layout.addWidget(self.open_folder_btn)
        self.button_layout.addWidget(self.save_btn)
        self.main_layout.addWidget(self.button_line)
        # Connect the save button to its slot
        self.save_btn.clicked.connect(self.save_images)
        # Set size policy for button line
        self.button_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Splitter for Image Preview Column and Categorization Column
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Image Preview Column
        self.image_label = QLabel()  # Label to display the current image
        self.image_preview_layout = QVBoxLayout()  # Layout for the image preview column
        self.image_preview_layout.addWidget(self.image_label)

        # Quote Board
        self.quote_label = QLabel("Quote Board", self)
        self.quote_label.setAlignment(Qt.AlignCenter)
        self.quote_label.setWordWrap(True)
        self.quote_label.setMaximumHeight(50)  # Adjust this value as needed for two lines of text
        self.image_preview_layout.addWidget(self.quote_label)

        self.quotes = self.load_quotes("quotes.txt")
        self.quote_timer = QTimer(self)
        self.quote_timer.timeout.connect(self.display_random_quote)
        self.quote_timer.start(15000)  # Change quotes every 5 seconds

        # Add the image preview layout to the splitter
        self.image_preview_widget = QWidget()  # Create a widget to hold the image preview layout
        self.image_preview_widget.setLayout(self.image_preview_layout)
        self.splitter.addWidget(self.image_preview_widget)

        # Categorization Column
        self.categorization_column = QWidget()
        self.category_column_layout = QVBoxLayout(self.categorization_column)

        # Timer and labels for image count and images per minute
        self.start_time = QDateTime.currentDateTime()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Update every second

        self.image_counter_label = QLabel("Images remaining: 0")
        self.timer_label = QLabel("Time elapsed: 00:00")
        self.images_per_minute_label = QLabel("Images per minute: 0")

        self.status_layout = QHBoxLayout()
        self.status_layout.addWidget(self.image_counter_label)
        self.status_layout.addWidget(self.timer_label)
        self.status_layout.addWidget(self.images_per_minute_label)
        self.image_counter_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.timer_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.images_per_minute_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.main_layout.addLayout(self.status_layout)

        # Sub-menu for New Category button
        self.sub_menu = QWidget()
        self.sub_menu_layout = QHBoxLayout(self.sub_menu)
        self.new_category_btn = QPushButton('New Category')
        self.new_category_btn.clicked.connect(self.create_new_category)
        self.sub_menu_layout.addWidget(self.new_category_btn)
        self.category_column_layout.addWidget(self.sub_menu)

        # Category grid layout inside a scroll area
        self.category_grid_widget = QWidget()
        self.category_layout = QGridLayout(self.category_grid_widget)
        self.category_scroll_area = QScrollArea()
        self.category_scroll_area.setWidgetResizable(True)
        self.category_scroll_area.setWidget(self.category_grid_widget)
        self.category_column_layout.addWidget(self.category_scroll_area)

        self.splitter.addWidget(self.categorization_column)
        self.main_layout.addWidget(self.splitter)  # Add the splitter only once
        self.splitter.setSizes([self.width() // 2, self.width() // 2])
        
        # Set Main Layout
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        self.image_files = []  # List to hold the paths of image files
        self.current_image_index = 0  # Index to keep track of the current image
        self.categories = {}  # Dictionary to hold categories

        self.open_folder_btn.clicked.connect(self.open_folder)

        self.category_counter = 0  # Counter to keep track of the created categories

        self.new_category_btn.clicked.connect(self.create_new_category)


    def create_new_category(self):
        category_widget = CategoryWidget()
        category_widget.assignImage.connect(self.assign_image_to_category)  # Connect custom signal to slot
        row, col = divmod(self.category_counter, 3)
        self.category_layout.addWidget(category_widget, row + 1, col)
        self.category_counter += 1

    def assign_image_to_category(self):
        category_widget = self.sender()
        category_name = category_widget.category_name_input.text().strip()  # strip leading/trailing whitespace
        if not category_name:
            QMessageBox.warning(self, "Empty Category Name", "Please enter a category name.")
            return
        current_image_path = self.image_files[self.current_image_index]
        self.categories_images.setdefault(category_name, []).append(current_image_path)  # Add image to categories_images

        if self.processed_images_count < len(self.image_files):
            pixmap = QPixmap(current_image_path)
            category_widget.set_image_preview(pixmap)
            self.show_next_image()
            self.processed_images_count += 1
            self.update_image_counter()
            # Start a single-shot timer to trigger a delayed rescale
            QTimer.singleShot(10, self.update_category_widths)  # 50 milliseconds delay

        else:
            # Optionally, show a message or take some other action when all images have been processed
            pass

    def update_image_counter(self):
        remaining_images = len(self.image_files) - self.processed_images_count
        self.image_counter_label.setText(f"Images remaining: {remaining_images}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.rescale_image()
        self.update_category_widths()

    def update_category_widths(self):
        column_width = self.categorization_column.width() // 3
        for i in range(self.category_layout.count()):
            widget = self.category_layout.itemAt(i).widget()
            if isinstance(widget, CategoryWidget):
                widget.update_width(column_width)

    def rescale_image(self):
        self.update_category_widths()  # Update category widths when the splitter is moved
        if self.image_files and self.processed_images_count < len(self.image_files):  # Check for unprocessed images
            pixmap = QPixmap(self.image_files[self.current_image_index])
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
        else:
            self.image_label.clear()

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.image_files = [f for f in os.listdir(folder_path) if f.endswith(('jpg', 'png', 'jpeg'))]
            self.image_files = [os.path.join(folder_path, f) for f in self.image_files]
            self.current_image_index = 0
            self.update_image_counter()
            self.show_current_image()
            print(self.image_files)  # Add this line to verify image file paths
            self.image_counter_label.setText(f"Images remaining: {len(self.image_files)}")

    def show_next_image(self):
        if self.processed_images_count < len(self.image_files):
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.show_current_image()
        else:
            self.image_label.clear()  # Clear the image preview if all images have been processed

    def show_current_image(self):
        if self.image_files and self.processed_images_count < len(self.image_files):
            pixmap = QPixmap(self.image_files[self.current_image_index])
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
        else:
            self.image_label.clear()  # Clear the image preview if all images have been processed

    def get_next_grid_position(self):
        # Placeholder method to get the next available grid position
        return 0, 0

    def save_images(self):
        save_directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if save_directory:
            for category_name, image_paths in self.categories_images.items():
                category_directory = os.path.join(save_directory, category_name)
                os.makedirs(category_directory, exist_ok=True)  # Create category directory if it doesn't exist
                for image_path in image_paths:
                    # Copy images to the category directory
                    destination_path = os.path.join(category_directory, os.path.basename(image_path))
                    shutil.copy(image_path, destination_path)
                    
                    # Handle text files
                    txt_file_path = image_path.rsplit('.', 1)[0] + '.txt'  # Replace image file extension with .txt
                    destination_txt_path = os.path.join(category_directory, os.path.basename(txt_file_path))
                    tags = []
                    if os.path.exists(txt_file_path):
                        with open(txt_file_path, 'r', encoding='utf-8') as file:
                            tags = file.read().split(', ')
                    tags.append(category_name)  # Append the category name as a tag
                    with open(destination_txt_path, 'w', encoding='utf-8') as file:
                        file.write(', '.join(tags))  # Write updated tags back to the text file

    def load_quotes(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().splitlines()
        return []

    def display_random_quote(self):
        if self.quotes:
            quote = random.choice(self.quotes)
            self.quote_label.setText(quote)

    def update_timer(self):
        elapsed = self.start_time.secsTo(QDateTime.currentDateTime())
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.timer_label.setText(f"Time elapsed: {minutes:02d}:{seconds:02d}")

        if elapsed > 0:
            images_per_minute = self.processed_images_count / (elapsed / 60)
            self.images_per_minute_label.setText(f"Images per minute: {images_per_minute:.2f}")


if __name__ == "__main__":
    app = QApplication([])

    # Load and apply stylesheet
    with open('style.css', 'r') as file:
        stylesheet = file.read()
        app.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()
    app.exec()