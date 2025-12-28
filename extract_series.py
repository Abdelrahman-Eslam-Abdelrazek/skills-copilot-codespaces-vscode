import csv
import json

def extract_series_data(csv_file_path, output_file_path='series_data.json'):
    """
    استخراج بيانات المسلسلات من ملف CSV
    
    Parameters:
    csv_file_path (str): مسار ملف CSV
    output_file_path (str): مسار ملف الإخراج (اختياري)
    """
    series_data = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                series = {
                    'title': row.get('title', ''),
                    'poster': row.get('image', ''),
                    'backdrop': row.get('backdropImage', ''),
                    'logo': row.get('logoImage', '') if row.get('logoImage') else None
                }
                series_data.append(series)
        
        print(f"✓ تم استخراج بيانات {len(series_data)} مسلسل بنجاح!")
        
        # حفظ البيانات في ملف JSON
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(series_data, json_file, ensure_ascii=False, indent=2)
        
        print(f"✓ تم حفظ البيانات في: {output_file_path}")
        
        # عرض أول 3 مسلسلات كمثال
        print("\n--- مثال على البيانات (أول 3 مسلسلات) ---")
        for i, series in enumerate(series_data[:3], 1):
            print(f"\nمسلسل #{i}:")
            print(f"  الاسم: {series['title']}")
            print(f"  البوستر: {series['poster']}")
            print(f"  الباك جراوند: {series['backdrop']}")
            print(f"  اللوجو: {series['logo'] if series['logo'] else 'غير متوفر'}")
        
        return series_data
        
    except FileNotFoundError:
        print(f"❌ خطأ: الملف '{csv_file_path}' غير موجود!")
        return None
    except Exception as e:
        print(f"❌ حدث خطأ: {str(e)}")
        return None


def save_as_txt(series_data, output_file='series_data.txt'):
    """حفظ البيانات كملف نصي"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, series in enumerate(series_data, 1):
                f.write(f"مسلسل #{i}\n")
                f.write(f"الاسم: {series['title']}\n")
                f.write(f"البوستر: {series['poster']}\n")
                f.write(f"الباك جراوند: {series['backdrop']}\n")
                f.write(f"اللوجو: {series['logo'] if series['logo'] else 'غير متوفر'}\n")
                f.write("-" * 80 + "\n\n")
        
        print(f"✓ تم حفظ البيانات كملف نصي: {output_file}")
    except Exception as e:
        print(f"❌ خطأ في الحفظ: {str(e)}")


def compare_data(series_data):
    """تحليل البيانات وعرض إحصائيات"""
    total = len(series_data)
    with_logo = sum(1 for s in series_data if s['logo'])
    with_backdrop = sum(1 for s in series_data if s['backdrop'])
    
    print(f"\n📊 إحصائيات تفصيلية:")
    print(f"  إجمالي المسلسلات: {total}")
    print(f"  مسلسلات بها لوجو: {with_logo} ({(with_logo/total*100):.1f}%)")
    print(f"  مسلسلات بدون لوجو: {total - with_logo} ({((total-with_logo)/total*100):.1f}%)")
    print(f"  مسلسلات بها باك جراوند: {with_backdrop} ({(with_backdrop/total*100):.1f}%)")
    print(f"  مسلسلات بدون باك جراوند: {total - with_backdrop} ({((total-with_backdrop)/total*100):.1f}%)")


# مثال على الاستخدام
if __name__ == "__main__":
    # استبدل "Series.csv" بمسار ملفك
    csv_file = "Series.csv"
    
    # استخراج البيانات
    series = extract_series_data(csv_file)
    
    if series:
        # حفظ كملف نصي أيضًا (اختياري)
        save_as_txt(series)
        
        # عرض إحصائيات مفصلة
        compare_data(series)