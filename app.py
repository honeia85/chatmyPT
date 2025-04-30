import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
import gc

def get_device():
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def init_model():
    model_name = "Qwen/Qwen-1_8B-Chat"
    device = get_device()
    print(f"Using device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        use_cache=True
    ).to(device).eval()
    
    model.generation_config = GenerationConfig.from_pretrained(
        model_name, 
        trust_remote_code=True,
        max_new_tokens=256,
        temperature=1.0,
        top_p=0.9,
        repetition_penalty=1.1
    )
    
    gc.collect()
    torch.mps.empty_cache() if device.type == 'mps' else torch.cuda.empty_cache()
    
    return model, tokenizer, device

class ChatBot:
    def __init__(self):
        self.model, self.tokenizer, self.device = init_model()
        self.history = []
        
    def chat(self, message, history):
        try:
            with torch.no_grad():
                response, self.history = self.model.chat(
                    self.tokenizer,
                    message,
                    history=self.history
                )
                
                # 메모리 최적화
                if len(self.history) > 5:
                    self.history = self.history[-5:]
                    gc.collect()
                    torch.mps.empty_cache() if self.device.type == 'mps' else torch.cuda.empty_cache()
                
                return response
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"

def create_demo():
    chatbot = ChatBot()
    
    with gr.Blocks(css="footer {visibility: hidden}") as demo:
        gr.Markdown("""
        # Qwen-1.8B 한국어 채팅 데모
        Qwen-1.8B 모델을 사용한 한국어 채팅 인터페이스입니다.
        """)
        
        chatbot_component = gr.Chatbot(
            label="대화 내역",
            bubble_full_width=False,
        )
        
        with gr.Row():
            msg = gr.Textbox(
                label="메시지",
                placeholder="메시지를 입력하세요...",
                scale=4
            )
            submit = gr.Button("전송", scale=1)
        
        clear = gr.Button("대화 내역 지우기")
        
        def respond(message, chat_history):
            bot_message = chatbot.chat(message, chat_history)
            chat_history.append((message, bot_message))
            return "", chat_history
        
        submit.click(
            respond,
            [msg, chatbot_component],
            [msg, chatbot_component],
        )
        
        msg.submit(
            respond,
            [msg, chatbot_component],
            [msg, chatbot_component],
        )
        
        clear.click(lambda: None, None, chatbot_component, queue=False)
        
    return demo

if __name__ == "__main__":
    demo = create_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        inbrowser=True
    ) 