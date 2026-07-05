import json
import os

def load_equipment(equipment_path: str) -> list:
    """Loads transcribed equipment list.
    If the file doesn't exist, returns a default mock list for the demo."""
    if os.path.exists(equipment_path):
        with open(equipment_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data.get("доступное_оборудование", [])
            except:
                pass
    return ["гидроциклоны", "классификаторы", "мельницы 3.3м", "мельницы 6м", "грохота", "флотомашины РИФ", "флотомашины Wemco"]

def parse_constraints(equipment_path: str, user_text: str = "") -> dict:
    """
    Combines the available equipment with user-provided constraints 
    like budget, time, or norms.
    """
    equipment = load_equipment(equipment_path)
    
    # We could use an LLM or regex to parse user_text, but for now 
    # we just pass it to the generator as raw text if simple parsing isn't strictly requested.
    # The prompt expects budget, сроки, нормативы. 
    # In a real system, we might ask LLM to extract these from the user prompt.
    
    budget = "Не ограничено"
    deadline = "Не ограничено"
    norms = "Без специфических норм"
    
    # Very basic dummy extraction just for the interface
    if "бюджет" in user_text.lower():
        budget = user_text # In production, extract exact value
    if "срок" in user_text.lower() or "месяц" in user_text.lower():
        deadline = user_text
        
    return {
        "доступное_оборудование": equipment,
        "бюджет": budget,
        "сроки": deadline,
        "нормативы": norms,
        "сырой_текст_ограничений": user_text
    }

if __name__ == "__main__":
    import sys
    eq_path = "factory/data/equipment.json"
    user_req = "бюджет 10 млн рублей, сроки 3 месяца"
    if len(sys.argv) > 1:
        user_req = sys.argv[1]
    
    print(json.dumps(parse_constraints(eq_path, user_req), ensure_ascii=False, indent=2))
