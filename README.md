KBEWSGIServer 这是一个KBEngine服务端demos资产库 的 WEB扩展 -- 使用Bottle 、 WSGIServer
========


联系方式   8181018@qq.com
------------------------------

基于 kbengine_demos_assets 项目的补充

## 开始



请将目录内容 复制添加 到 kbengine_demos_assets 目录

额外修改文件：

	1、kbengine_demos_assets/scripts/entities.xml  在 root 下添加：
			
		<WebManager/>


	2、scripts/base/kbemain.py 在 onBaseAppReady 方法 添加以下 用以自动启动WEB管理器

		KBEngine.createEntityLocally("WebManager", {})



## bottle   WEB框架   


## KBEWSGIServer   HTTP功能实现 

	使用  WSGIREF 自建SOCKET服务器 
	使用  registerReadFileDescriptor 监听连接请求


## BottleRouter 业务处理  

	一些示例
	返回值为 dict 且 key code的值 为wait时 客户端 http 连接将被挂起
	必须 在返回之前调用  root.webmgr.wait() 使当前 http连接 进入等待超时队例 默认5秒超时

	ps:无跨进程调用可以不使用挂起操作，直接进行输出

## WebManager 数据处理 
	onTimer 中处理超时连接
	远程接口 remoteCall 在跨进程调用后 回调使用

	如: Base.BottleRouter -> Base.WebManager ->  Cell.Avater ->  Base.WebManager 



