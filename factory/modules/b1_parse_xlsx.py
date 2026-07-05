import openpyxl
import json
import os
import sys

def clean_val(val):
    if val is None or val == "#REF!" or isinstance(val, str):
        return None
    return float(val)

def parse_xlsx(filepath: str) -> dict:
    wb = openpyxl.load_workbook(filepath, data_only=True)
    sheet = wb.active
    
    # Extract factory name from filename if possible
    basename = os.path.basename(filepath)
    factory_name = basename.replace("Хвосты", "").replace(".xlsx", "").strip()
    if not factory_name:
        factory_name = "Неизвестно"
        
    result = {
        "фабрика": factory_name,
        "потоки": {},
        "классы": []
    }
    
    # 1. Потоки
    for row_idx in range(1, 20):
        name = sheet.cell(row=row_idx, column=2).value
        if name and isinstance(name, str):
            name = name.strip()
            if "Шихта руд" in name:
                result["потоки"]["переработка_смт"] = clean_val(sheet.cell(row=row_idx, column=3).value)
            elif "Отвальные хвосты" in name:
                result["потоки"]["хвосты_смт"] = clean_val(sheet.cell(row=row_idx, column=3).value)
                result["потоки"]["никель_в_хвостах_т"] = clean_val(sheet.cell(row=row_idx, column=5).value)
                result["потоки"]["медь_в_хвостах_т"] = clean_val(sheet.cell(row=row_idx, column=7).value)
                
    # 2. Общая таблица классов (строки примерно 19-30)
    # Найдём заголовок "Класс крупности, мкм"
    class_summary_row = None
    for row_idx in range(10, 40):
        val = sheet.cell(row=row_idx, column=2).value
        if val and isinstance(val, str) and "Класс крупности" in val:
            class_summary_row = row_idx
            break
            
    classes_summary = {}
    if class_summary_row:
        for row_idx in range(class_summary_row + 1, class_summary_row + 15):
            cls_name = sheet.cell(row=row_idx, column=2).value
            if not cls_name or (isinstance(cls_name, str) and "Итого" in cls_name):
                if isinstance(cls_name, str) and "Итого" in cls_name:
                    break
                continue
            
            if isinstance(cls_name, str):
                cls_name = cls_name.strip()
                
            classes_summary[cls_name] = {
                "доля_класса_%": clean_val(sheet.cell(row=row_idx, column=3).value),
                "никель_т": clean_val(sheet.cell(row=row_idx, column=5).value),
                "медь_т": clean_val(sheet.cell(row=row_idx, column=7).value)
            }

    # 3. Минералогия по классам
    # Ищем блоки классов, начиная ниже таблицы summary
    start_row = class_summary_row + 8 if class_summary_row else 15
    for row_idx in range(start_row, sheet.max_row + 1):
        val = sheet.cell(row=row_idx, column=2).value
        if not val or not isinstance(val, str):
            continue
            
        val_strip = val.strip()
        # Ищем названия классов в точности как в summary, или "+125 мкм"
        matched_cls = None
        for cls_name in classes_summary.keys():
            if val_strip.startswith(cls_name):
                matched_cls = cls_name
                break
                
        if matched_cls:
            # Нашли блок класса. Минералогия идет со следующей строки или через одну.
            # Будем искать вниз до "Не извлекаемый металл"
            
            class_data = {
                "класс": matched_cls,
                "доля_класса_%": classes_summary[matched_cls]["доля_класса_%"],
                "никель_т": classes_summary[matched_cls]["никель_т"],
                "медь_т": classes_summary[matched_cls]["медь_т"],
                "минералогия": {}
            }
            
            for sub_row_idx in range(row_idx + 1, row_idx + 30):
                sub_val = sheet.cell(row=sub_row_idx, column=2).value
                if not sub_val or not isinstance(sub_val, str):
                    continue
                sub_val = sub_val.strip()
                
                ni_t = clean_val(sheet.cell(row=sub_row_idx, column=5).value)
                cu_t = clean_val(sheet.cell(row=sub_row_idx, column=7).value)
                
                if "Извлекаемый металл" == sub_val:
                    class_data["никель_извлекаемый_т"] = ni_t
                    class_data["медь_извлекаемый_т"] = cu_t
                elif "Не извлекаемый металл" == sub_val:
                    class_data["никель_неизвлекаемый_т"] = ni_t
                    class_data["медь_неизвлекаемый_т"] = cu_t
                    break # Конец блока
                elif sub_val not in ["Потери (расписать)", "Свободный слот", "Итого (проверка)"]:
                    # Это минерал
                    key = sub_val.lower().replace(" ", "_").replace("/", "_")
                    class_data["минералогия"][f"{key}_никель_т"] = ni_t
                    class_data["минералогия"][f"{key}_медь_т"] = cu_t
            
            result["классы"].append(class_data)

    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python b1_parse_xlsx.py <path_to_xlsx> [out_json]")
        sys.exit(1)
        
    res = parse_xlsx(sys.argv[1])
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"Saved to {sys.argv[2]}")
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))
