import requests
from datetime import datetime
from chatgpt_on_wechat.plugins import *
from chatgpt_on_wechat.common import *
from config import conf

@plugins.register(name="Zabbix", desc="A plugin that checks Zabbix for problems", version="0.1", author="YourName", desire_priority=10)
class Zabbix(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Zabbix] inited")
        
        # 从配置文件加载Zabbix API详情
        self.zabbix_url = conf().get("zabbix_url")
        self.zabbix_api_token = conf().get("zabbix_api_token")
        
        if not self.zabbix_url or not self.zabbix_api_token:
            raise ValueError("配置文件中缺少Zabbix API配置信息")

    def get_zabbix_problems(self):
        payload = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": "extend",
                "recent": True,
                "sortfield": ["eventid"],
                "sortorder": "DESC"
            },
            "id": 1,
            "auth": self.zabbix_api_token
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.zabbix_api_token}"
        }
        response = requests.post(self.zabbix_url, json=payload, headers=headers)
        result = response.json()
        if 'result' in result:
            return result['result']
        else:
            raise Exception(f"从Zabbix获取问题失败: {result}")

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return
        content = e_context['context'].content.strip().lower()
        if content == "zabbix status":
            try:
                problems = self.get_zabbix_problems()
                if not problems:
                    reply_content = "Zabbix中没有检测到问题。"
                else:
                    reply_content = "Zabbix中的当前问题:\n"
                    for problem in problems:
                        time = datetime.fromtimestamp(int(problem['clock'])).strftime('%Y-%m-%d %H:%M:%S')
                        reply_content += f"[{time}] {problem['name']}\n"
                reply = Reply(ReplyType.TEXT, reply_content)
            except Exception as e:
                reply = Reply(ReplyType.ERROR, f"获取Zabbix状态时出错: {str(e)}")
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS

