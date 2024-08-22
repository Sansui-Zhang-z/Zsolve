# Zsolve

这是一个模仿Stegsolve的练习项目，可以实现按RGBA通道查看黑白图，提取LSB、MSB隐写

字符串，扫描识别二维码或条形码，并有UI界面。

<img src="https://raw.githubusercontent.com//Sansui-Zhang-z/Zsolve/edit/main/Show.png" />

### 原理说明

图片是由像素点组成，每一个像素点按照不同模式存储信息，仅修改每个像素点中少量信息即可进行信息写入，同时几乎不改变图像效果和大小，从而实现图像隐写。

本项目以理解图像隐写原理为目的，模仿Stegsolve工具实现一部分提取隐写信息功能，同时学习使用PyQt库。

### 库

1. PyQt5
2. Image
3. decode

### 使用方法

运行后点击选择文件，等待上方进度条加载完毕后即可查看

### TODO

目前只有单一的几个提取信息功能，后续可以添加隐写功能。

加载通道的部分速度很差，需要继续优化
