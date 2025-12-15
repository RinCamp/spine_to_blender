# # spine-to-blender

![Anim](https://github.com/user-attachments/assets/756d70ff-3dc2-42c7-b20b-289163666614)

## README  

[中文](README.md) | [English (Using Translate)](README-en.md) 

## 安装

(推荐) 直接下载zip源码 | Releases选择文件下载  

Blender偏好设置 > 插件 > 安装 [spine-to-blender-main.zip]  

## 导入

Blender版本: 5.0+ | Spine版本: 3.8 / 4.2  

1.选择对应的文件目录 .json / .atlas / .png  

2.输入导入哪个皮肤  

3.自定义导入的角色名  

4.点击 [ 导入Spine ]   

## 注意

此插件通常只能处理比较简单的项目, 且只导入骨骼与网格

皮肤的附件(skins-attachments), 若类型均为"region" (网格只使用1个面/4个顶点)

选择图集文件夹并使用 <Re:Dive> 类型导入

## 使用插槽

1.在导入界面的 [ 导入Spine ] 左侧的按钮可以导入插槽数据  

2.在插槽界面的 [ 插槽列表 ] 右侧的按钮也可打开隐藏的简化导入界面  

3.选择目标骨架, 输入对应的角色名, 以获取插槽数据中的骨骼/网格  

4.可以点击名称左侧的光标进行选择该骨骼/网格  

5.(可以通过网格的名称快速查找相关内容 "角色名-插槽-附件")  

## 导入动画 (仅支持Blender4.4后的版本)

目前仅支持导入位置/缩放/旋转的关键帧

只导入动作本身, 可使用非线性动画, 选择动作与插槽

关于Blender4.4版本的动画系统说明

https://docs.blender.org/manual/en/4.4/animation/actions.html


## 关于Spine导出Json格式

http://esotericsoftware.com/spine-json-format

## 已知问题

无法正常导入使用路径约束的骨骼

安装其它版本时, 卸载插件后, 需要重启Blender (开关插件时无影响)

切换Blender语言时, 需要重启插件才能正确更新部分UI翻译

## 界面预览

<img width="1601" height="1256" alt="info_zh_cn" src="https://github.com/user-attachments/assets/e49cacf0-443f-46e3-8112-8ab656f3dfa7" />
