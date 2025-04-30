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
    # 더 작은 Qwen 모델 사용
    model_name = "Qwen/Qwen-1_8B-Chat"
    device = get_device()
    print(f"Using device: {device}")
    
    # 토크나이저 초기화
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        trust_remote_code=True
    )
    
    # 모델 로드 및 최적화 설정
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        use_cache=True
    ).to(device).eval()
    
    # 생성 설정 최적화
    model.generation_config = GenerationConfig.from_pretrained(
        model_name, 
        trust_remote_code=True,
        max_new_tokens=256,
        temperature=1.0,
        top_p=0.9,
        repetition_penalty=1.1
    )
    
    # 메모리 최적화
    gc.collect()
    torch.mps.empty_cache() if device.type == 'mps' else torch.cuda.empty_cache()
    
    return model, tokenizer, device

def chat():
    try:
        model, tokenizer, device = init_model()
        print("채팅을 시작합니다. 종료하려면 'quit'를 입력하세요.")
        history = []
        
        while True:
            user_input = input("\n사용자: ")
            if user_input.lower() == 'quit':
                break
            
            try:
                with torch.no_grad():
                    response, history = model.chat(
                        tokenizer,
                        user_input,
                        history=history
                    )
                print(f"\n어시스턴트: {response}")
                
                # 메모리 최적화
                if len(history) > 5:
                    history = history[-5:]
                    gc.collect()
                    torch.mps.empty_cache() if device.type == 'mps' else torch.cuda.empty_cache()
                    
            except Exception as e:
                print(f"\n응답 생성 중 오류가 발생했습니다: {str(e)}")
                continue
    except Exception as e:
        print(f"\n모델 초기화 중 오류가 발생했습니다: {str(e)}")
    finally:
        # 종료 시 메모리 정리
        if 'model' in locals():
            del model
            gc.collect()
            torch.mps.empty_cache() if device.type == 'mps' else torch.cuda.empty_cache()

if __name__ == "__main__":
    chat() 