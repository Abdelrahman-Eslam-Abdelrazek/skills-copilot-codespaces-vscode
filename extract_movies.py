import csv
import json

def extract_movies_data(csv_file_path, output_file_path='movies_data.json'):
    """
    استخراج بيانات الأفلام من ملف CSV
    
    Parameters:
    csv_file_path (str): مسار ملف CSV
    output_file_path (str): مسار ملف الإخراج (اختياري)
    """
    movies_data = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                movie = {
                    'title': row.get('title', ''),
                    'poster': row.get('image', ''),
                    'backdrop': row.get('backdropImage', ''),
                    'logo': row.get('logoImage', '') if row.get('logoImage') else None
                }
                movies_data.append(movie)
        
        print(f"✓ تم استخراج بيانات {len(movies_data)} فيلم بنجاح!")
        
        # حفظ البيانات في ملف JSON
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(movies_data, json_file, ensure_ascii=False, indent=2)
        
        print(f"✓ تم حفظ البيانات في: {output_file_path}")
        
        # عرض أول 3 أفلام كمثال
        print("\n--- مثال على البيانات (أول 3 أفلام) ---")
        for i, movie in enumerate(movies_data[:3], 1):
            print(f"\nفيلم #{i}:")
            print(f"  الاسم: {movie['title']}")
            print(f"  البوستر: {movie['poster']}")
            print(f"  الباك جراوند: {movie['backdrop']}")
            print(f"  اللوجو: {movie['logo'] if movie['logo'] else 'غير متوفر'}")
        
        return movies_data
        
    except FileNotFoundError:
        print(f"❌ خطأ: الملف '{csv_file_path}' غير موجود!")
        return None
    except Exception as e:
        print(f"❌ حدث خطأ: {str(e)}")
        return None


def save_as_txt(movies_data, output_file='movies_data.txt'):
    """حفظ البيانات كملف نصي"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, movie in enumerate(movies_data, 1):
                f.write(f"فيلم #{i}\n")
                f.write(f"الاسم: {movie['title']}\n")
                f.write(f"البوستر: {movie['poster']}\n")
                f.write(f"الباك جراوند: {movie['backdrop']}\n")
                f.write(f"اللوجو: {movie['logo'] if movie['logo'] else 'غير متوفر'}\n")
                f.write("-" * 80 + "\n\n")
        
        print(f"✓ تم حفظ البيانات كملف نصي: {output_file}")
    except Exception as e:
        print(f"❌ خطأ في الحفظ: {str(e)}")


# مثال على الاستخدام
if __name__ == "__main__":
    # استبدل "movies.csv" بمسار ملفك
    csv_file = "Movies.csv"
    
    # استخراج البيانات
    movies = extract_movies_data(csv_file)
    
    # حفظ كملف نصي أيضًا (اختياري)
    if movies:
        save_as_txt(movies)
        
        # إحصائيات
        print(f"\n📊 إحصائيات:")
        print(f"  إجمالي الأفلام: {len(movies)}")
        
        movies_with_logo = sum(1 for m in movies if m['logo'])
        print(f"  أفلام بها لوجو: {movies_with_logo}")
        print(f"  أفلام بدون لوجو: {len(movies) - movies_with_logo}")