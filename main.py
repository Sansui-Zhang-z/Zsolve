# -----实现的功能-----
# 分离图片RGBA四个通道的8位二进制值，并生成对应的黑白图显示在窗口内（共4通道*8位=32张）
# 提取原图片的LSB隐写字符串
# 提取原图片的MSB隐写字符串
# 识别当前显示图片中的二维码/条形码
#
# -----优化内容-----
# 通过位运算代替原来的下标访问获取位值，极大提高了通道处理速度
# 添加了隐写提取实时字节数显示
# 添加了鼠标失效时间，防止长时间处理过程中点击鼠标出现未响应提示
#
# -----缺陷-----
# LSB及MSB隐写提取算法没变依然很慢，不过可以通过位运算进行优化
#
# -----优点-----
# 界面布局还算合理，使用比较方便，可以适应图片分辨率自由缩放
# 添加了进度条控件和显示当前像素点读取数量的label控件，等待的时候不会觉得是死机了=，=
# 虽然读取慢，但是读取通道结束后，不再有复杂的运算，所有控件都能瞬时响应
# 除去UI的必需包，基本上没有导入太多的包，几乎都是手写处理方法（这可能算是缺点=。=，效率低）

import sys

# 可视化的包
from PyQt5.QtGui import QPixmap, QImage
from UI import Ui_Form
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox

# 图像通道处理的包
from PIL import Image

# 二维码/条形码识别的包
from pyzbar.pyzbar import decode


class MyMainForm(QWidget, Ui_Form):
    # 基本的初始化
    def __init__(self, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)
        self.connected()
        self.tip_list = ['Normal Image',
                         'Alpha plane 7', 'Alpha plane 6', 'Alpha plane 5', 'Alpha plane 4',
                         'Alpha plane 3', 'Alpha plane 2', 'Alpha plane 1', 'Alpha plane 0',
                         'Red plane 7', 'Red plane 6', 'Red plane 5', 'Red plane 4',
                         'Red plane 3', 'Red plane 2', 'Red plane 1', 'Red plane 0',
                         'Green plane 7', 'Green plane 6', 'Green plane 5', 'Green plane 4',
                         'Green plane 3', 'Green plane 2', 'Green plane 1', 'Green plane 0',
                         'Blue plane 7', 'Blue plane 6', 'Blue plane 5', 'Blue plane 4',
                         'Blue plane 3', 'Blue plane 2', 'Blue plane 1', 'Blue plane 0']
        self.index = -1
        self.ignore_mouse_click = False
        self.isImage = False
        self.image = []
        self.rgba_bin_data = []
        self.lsbBin_src = ''
        self.msbBin_src = ''
        self.lsb_src = ''
        self.msb_src = ''
        self.width = None
        self.height = None
        self.state_bar.setVisible(False)

    # 控件自定义槽函数的集合
    def connected(self):
        self.choose_button.clicked.connect(self.openImage)
        self.next_button.clicked.connect(self.nextClicked)
        self.back_button.clicked.connect(self.backClicked)
        self.LSB_button.clicked.connect(self.LSBclicked)
        self.MSB_button.clicked.connect(self.MSBclicked)
        self.saveBin_button.clicked.connect(self.saveBinlicked)
        self.OCR_button.clicked.connect(self.OCRclicked)

    def ignore_mouse_clicks(self, ignore=True):
        self.ignore_mouse_click = ignore

    # 向前切换图片按钮的槽函数
    def backClicked(self):
        if self.isImage:
            self.index -= 1
            if self.index < 0:
                self.index = len(self.tip_list) - 1
            self.nowType_label.setText(self.tip_list[self.index])
            self.showInLabel()

    # 向后切换图片按钮的槽函数
    def nextClicked(self):
        if self.isImage:
            self.index += 1
            if self.index >= len(self.tip_list):
                self.index = 0
            self.nowType_label.setText(self.tip_list[self.index])
            self.showInLabel()

    # 打开图片按钮槽函数
    def openImage(self):
        imgName, imgType = QFileDialog.getOpenFileName(self, '选择图片', '', '*.png;;*.jpg;;*.bmp;;ALL File(*)')
        if imgName:
            self.move(0, 0)
            self.ignore_mouse_click = True
            self.isImage = True
            self.image.clear()
            image_tmp = Image.open(imgName)
            self.width, self.height = image_tmp.size
            self.image.append(image_tmp.convert("RGBA"))
            self.index = 0
            self.showInLabel()
            self.nowType_label.setText(self.tip_list[self.index])
            self.getRGBAdata()
            self.ignore_mouse_click = False

    # 在控件内显示当前图片
    def showInLabel(self):
        if self.image[self.index]:
            img_data = self.image[self.index].convert("RGBA").tobytes()
            q_image = QImage(img_data, self.width, self.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)

    # 分离获取ARGB通道数据
    def getRGBAdata(self):
        rgba_data = self.image[0].getdata()
        self.rgba_bin_data.clear()
        for pixel in rgba_data:
            pixel_bin = []
            for i in pixel:
                pixel_bin.append(bin(i)[2:].zfill(8))
            self.rgba_bin_data.append(pixel_bin)
        for i in range(4 * 8):
            self.image.append(Image.new(mode='1', size=(self.width, self.height)))
        self.state_bar.setVisible(True)
        self.state_bar.reset()
        for y in range(self.height):
            for x in range(self.width):
                r_pixel = self.image[0].getpixel((x, y))[0]
                g_pixel = self.image[0].getpixel((x, y))[1]
                b_pixel = self.image[0].getpixel((x, y))[2]
                a_pixel = self.image[0].getpixel((x, y))[3]
                for j in range(1, 9):
                    r_bit = (r_pixel >> (8 - j)) & 1
                    g_bit = (g_pixel >> (8 - j)) & 1
                    b_bit = (b_pixel >> (8 - j)) & 1
                    a_bit = (a_pixel >> (8 - j)) & 1

                    r_new_bit = 255 if r_bit == 1 else 0
                    g_new_bit = 255 if g_bit == 1 else 0
                    b_new_bit = 255 if b_bit == 1 else 0
                    a_new_bit = 255 if a_bit == 1 else 0

                    self.image[j].putpixel((x, y), a_new_bit)
                    self.image[j + 8].putpixel((x, y), r_new_bit)
                    self.image[j + 16].putpixel((x, y), g_new_bit)
                    self.image[j + 24].putpixel((x, y), b_new_bit)
                nums = y * self.width + x + 1
                self.state_label.setText(f'{nums}/{self.width * self.height}像素点')
                self.state_label.update()
                value = int(nums * 100 / (self.width * self.height))
                self.state_bar.setValue(value)

    # LSB提取按钮槽函数
    def LSBclicked(self):
        self.ignore_mouse_click = True
        self.state_label.clear()
        self.state_label.setText('正在读取低位数据')
        self.state_label.update()
        self.lsbBin_src = ''
        for i in self.rgba_bin_data:
            for j in i[:3]:
                self.lsbBin_src += j[7]
        self.lsb_src = ''
        for i in range(0, len(self.lsbBin_src), 8):
            num = int(self.lsbBin_src[i:i + 8], 2)
            if 31 < num < 127:
                self.lsb_src += chr(num)
            else:
                self.lsb_src += '.'
            state_src = f'已提取{len(self.lsb_src)}字节内容'
            self.state_label.setText(state_src)
            self.state_label.update()
        self.res_textEdit.setText(self.lsb_src)
        self.ignore_mouse_click = False

    # MSB提取按钮槽函数
    def MSBclicked(self):
        self.ignore_mouse_click = True
        self.state_label.clear()
        self.state_label.setText('正在读取低位数据')
        self.state_label.update()
        self.msbBin_src = ''
        for i in self.rgba_bin_data:
            for j in i[:3]:
                self.msbBin_src += j[0]
        self.msb_src = ''
        for i in range(0, len(self.msbBin_src), 8):
            num = int(self.msbBin_src[i:i + 8], 2)
            if 31 < num < 127:
                self.msb_src += chr(num)
            else:
                self.msb_src += '.'
            state_src = f'已提取{len(self.msb_src)}字节内容'
            self.state_label.setText(state_src)
            self.state_label.update()
        self.res_textEdit.setText(self.msb_src)
        self.ignore_mouse_click = False

    # 二维码/条形码识别按钮槽函数
    def OCRclicked(self):
        decocdeQR = decode(self.image[self.index])
        if decocdeQR:
            res_src = decocdeQR[0].data.decode('ascii')
        else:
            res_src = '未识别到二维码或条形码'
        self.res_textEdit.clear()
        self.res_textEdit.setText(res_src)

    def saveBinlicked(self):
        if self.lsb_src or self.msb_src:
            options = QFileDialog.Options()
            folder_path = QFileDialog.getExistingDirectory(self, '选择保存文件夹', '', options=options)
            if folder_path:
                if self.lsb_src:
                    with open(file=folder_path + '/lsb', mode='wb') as f:
                        lsb_bin_data = bytes([int(self.lsbBin_src[i:i + 8], 2) for i in range(0, len(self.lsbBin_src), 8)])
                        f.write(lsb_bin_data)
                if self.msb_src:
                    with open(file=folder_path + '/msb', mode='wb') as f:
                        msb_bin_data = bytes([int(self.msbBin_src[i:i + 8], 2) for i in range(0, len(self.msbBin_src), 8)])
                        f.write(msb_bin_data)
                QMessageBox.information(self, '提示信息', '已将提取数据保存到文件夹下！')
        else:
            QMessageBox.critical(self, '运行错误', '尚未提取LSB或MSB数据，请点击按钮提取！')


# 主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyMainForm()
    myWin.show()
    myWin.ignore_mouse_clicks(ignore=True)
    sys.exit(app.exec_())
