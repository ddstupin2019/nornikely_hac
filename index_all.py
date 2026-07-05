import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_my.run_tests import load_all_to_rag

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    example_dir = os.path.join(base_dir, "exepmle")
    print(f"Индексация директории: {example_dir}")
    load_all_to_rag(example_dir)
    print("Индексация завершена!")

if __name__ == "__main__":
    main()
