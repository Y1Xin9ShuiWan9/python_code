import json
import os
import threading
from pynput import keyboard
from pynput.keyboard import Controller, Key
import time

class TextExpanderCLI:
    def __init__(self):
        # 数据存储
        self.data_file = "text_expander_data.json"
        self.texts = self.load_data()
        
        # 键盘控制器
        self.keyboard = Controller()
        self.listener = None
        self.running = False
        self.input_buffer = []
        self.buffer_timeout = 2  # 输入缓冲超时时间(秒)
        self.last_input_time = time.time()
        
        # 启动监听线程
        self.start_listener()
        self.start_buffer_cleaner()
        
        # 显示欢迎信息
        self.show_welcome()

    def load_data(self):
        """加载保存的文案数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                print("数据文件损坏，将创建新文件")
                return {}
        return {}

    def save_data(self):
        """保存文案数据到JSON文件"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.texts, f, ensure_ascii=False, indent=2)
        print("数据已保存")

    def show_welcome(self):
        """显示欢迎信息和操作说明"""
        print("="*50)
        print("      自定义文案输入工具 (命令行版)")
        print("="*50)
        print("操作命令:")
        print("  add [关键词] [文案内容] - 添加自定义文案")
        print("  list                   - 列出所有文案")
        print("  delete [关键词]        - 删除指定文案")
        print("  save                   - 保存数据")
        print("  exit                   - 退出程序")
        print("="*50)
        print("提示: 在任何应用中输入关键词后将自动替换为对应文案")
        print("="*50)

    def add_text(self, key, content):
        """添加文案"""
        if not key or not content:
            print("错误: 关键词和内容不能为空")
            return
            
        self.texts[key] = content
        print(f"已添加: {key} -> {content[:20]}...")

    def delete_text(self, key):
        """删除文案"""
        if key in self.texts:
            del self.texts[key]
            print(f"已删除: {key}")
        else:
            print(f"错误: 未找到关键词 '{key}'")

    def list_texts(self):
        """列出所有文案"""
        if not self.texts:
            print("没有保存的文案")
            return
            
        print("\n自定义文案列表:")
        print("-"*30)
        for i, (key, content) in enumerate(self.texts.items(), 1):
            print(f"{i}. {key} -> {content[:30]}{'...' if len(content) > 30 else ''}")
        print("-"*30)

    def on_press(self, key):
        """键盘按下事件处理"""
        try:
            current_time = time.time()
            # 超时清理缓冲区
            if current_time - self.last_input_time > self.buffer_timeout:
                self.input_buffer = []
                
            self.last_input_time = current_time
            
            # 处理字符按键
            if hasattr(key, 'char') and key.char is not None:
                self.input_buffer.append(key.char.lower())
                # 检查是否匹配任何关键词
                self.check_triggers()
                
            # 处理退格键
            elif key == Key.backspace and self.input_buffer:
                self.input_buffer.pop()
                
        except Exception as e:
            print(f"按键处理错误: {e}")

    def check_triggers(self):
        """检查输入缓冲区是否匹配任何触发关键词"""
        buffer_str = ''.join(self.input_buffer)
        
        # 从长到短检查所有关键词
        for trigger in sorted(self.texts.keys(), key=len, reverse=True):
            if buffer_str.endswith(trigger):
                # 删除触发关键词
                for _ in range(len(trigger)):
                    self.keyboard.press(Key.backspace)
                    self.keyboard.release(Key.backspace)
                # 输入替换文本
                self.keyboard.type(self.texts[trigger])
                # 清空缓冲区
                self.input_buffer = []
                break

    def start_listener(self):
        """启动键盘监听线程"""
        self.running = True
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def start_buffer_cleaner(self):
        """启动缓冲区清理线程"""
        def buffer_cleaner():
            while self.running:
                time.sleep(1)
                if time.time() - self.last_input_time > self.buffer_timeout:
                    self.input_buffer = []
                    
        threading.Thread(target=buffer_cleaner, daemon=True).start()

    def stop_listener(self):
        """停止键盘监听"""
        self.running = False
        if self.listener:
            self.listener.stop()

    def run_cli(self):
        """运行命令行界面"""
        while True:
            try:
                command = input("\n请输入命令: ").strip()
                if not command:
                    continue
                    
                parts = command.split(maxsplit=2)
                cmd = parts[0].lower()
                
                if cmd == 'add' and len(parts) >= 3:
                    self.add_text(parts[1], parts[2])
                elif cmd == 'list':
                    self.list_texts()
                elif cmd == 'delete' and len(parts) >= 2:
                    self.delete_text(parts[1])
                elif cmd == 'save':
                    self.save_data()
                elif cmd == 'exit':
                    self.save_data()
                    print("程序已退出")
                    self.stop_listener()
                    break
                else:
                    print("错误: 无效命令，请查看帮助")
                    
            except KeyboardInterrupt:
                self.save_data()
                self.stop_listener()
                break
            except Exception as e:
                print(f"命令执行错误: {e}")

if __name__ == "__main__":
    app = TextExpanderCLI()
    app.run_cli()
    print("自定义文案输入工具(CLI版).py 执行成功")