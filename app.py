import sys
import os
import threading
import webbrowser
import time
from tkinter import Tk, Label, Button, Frame, messagebox
from tkinter.ttk import Progressbar

def start_server():
    os.chdir(os.path.dirname(sys.argv[0]))
    
    from api.routes import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def open_browser():
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("无人机前沿情报采集系统")
        self.geometry("500x300")
        self.resizable(False, False)
        
        self.status = Label(self, text="初始化...", font=('微软雅黑', 12))
        self.status.pack(pady=20)
        
        self.progress = Progressbar(self, orient='horizontal', length=400, mode='indeterminate')
        self.progress.pack(pady=10)
        
        self.info_frame = Frame(self)
        self.info_frame.pack(pady=10)
        
        self.url_label = Label(self.info_frame, text="访问地址: ", font=('微软雅黑', 10))
        self.url_label.pack(side='left')
        
        self.url_link = Label(self.info_frame, text="http://localhost:5000", 
                            font=('微软雅黑', 10, 'underline'), fg='blue', cursor='hand2')
        self.url_link.pack(side='left')
        self.url_link.bind('<Button-1>', lambda e: webbrowser.open('http://localhost:5000'))
        
        self.btn_frame = Frame(self)
        self.btn_frame.pack(pady=20)
        
        self.open_btn = Button(self.btn_frame, text="打开浏览器", command=self.open_browser_click,
                            font=('微软雅黑', 10), width=12)
        self.open_btn.pack(side='left', padx=5)
        
        self.exit_btn = Button(self.btn_frame, text="退出", command=self.exit_app,
                            font=('微软雅黑', 10), width=12)
        self.exit_btn.pack(side='left', padx=5)
        
        self.protocol("WM_DELETE_WINDOW", self.exit_app)
        
        self.start_server_thread()
    
    def start_server_thread(self):
        self.progress.start()
        self.status.config(text="启动服务器...")
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        self.check_server()
    
    def check_server(self):
        try:
            import urllib.request
            urllib.request.urlopen('http://localhost:5000', timeout=1)
            self.status.config(text="✅ 服务器启动成功！")
            self.progress.stop()
        except:
            self.after(500, self.check_server)
    
    def open_browser_click(self):
        webbrowser.open('http://localhost:5000')
    
    def exit_app(self):
        if messagebox.askokcancel("退出", "确定要退出吗？服务器将停止运行。"):
            self.destroy()

if __name__ == '__main__':
    app = App()
    app.mainloop()
