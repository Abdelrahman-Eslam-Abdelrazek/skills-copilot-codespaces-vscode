import os
import json
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import time

class ImageConverter:
    def __init__(self, quality=80, max_width=1920):
        """
        quality: جودة الصورة (1-100) - كل ما قل الرقم كل ما الحجم صغر
        max_width: أقصى عرض للصورة بالبكسل
        """
        self.quality = quality
        self.max_width = max_width
        self.success_count = 0
        self.failed_count = 0
        self.total_original_size = 0
        self.total_converted_size = 0
        
    def download_image(self, url, timeout=10):
        """تحميل الصورة من الرابط"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"❌ فشل تحميل: {url[:50]}... - {str(e)}")
            return None
    
    def resize_image(self, img):
        """تصغير حجم الصورة إذا كانت كبيرة"""
        width, height = img.size
        if width > self.max_width:
            ratio = self.max_width / width
            new_height = int(height * ratio)
            img = img.resize((self.max_width, new_height), Image.Resampling.LANCZOS)
        return img
    
    def convert_to_webp(self, image_data, output_path):
        """تحويل الصورة إلى WebP"""
        try:
            # فتح الصورة
            img = Image.open(BytesIO(image_data))
            
            # تحويل إلى RGB إذا كانت RGBA
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # تصغير الحجم
            img = self.resize_image(img)
            
            # حفظ كـ WebP
            img.save(output_path, 'WEBP', quality=self.quality, method=6)
            
            return True
        except Exception as e:
            print(f"❌ فشل التحويل: {str(e)}")
            return False
    
    def process_single_image(self, url, output_dir, filename):
        """معالجة صورة واحدة"""
        if not url or url == 'None':
            return None
        
        try:
            # تحميل الصورة
            image_data = self.download_image(url)
            if not image_data:
                self.failed_count += 1
                return None
            
            original_size = len(image_data)
            self.total_original_size += original_size
            
            # إنشاء المجلد إذا لم يكن موجود
            os.makedirs(output_dir, exist_ok=True)
            
            # مسار الحفظ
            output_path = os.path.join(output_dir, filename)
            
            # التحويل
            if self.convert_to_webp(image_data, output_path):
                converted_size = os.path.getsize(output_path)
                self.total_converted_size += converted_size
                self.success_count += 1
                
                reduction = ((original_size - converted_size) / original_size) * 100
                print(f"✓ {filename}: {original_size/1024:.1f}KB → {converted_size/1024:.1f}KB (توفير {reduction:.1f}%)")
                
                return output_path
            else:
                self.failed_count += 1
                return None
                
        except Exception as e:
            print(f"❌ خطأ في معالجة {filename}: {str(e)}")
            self.failed_count += 1
            return None
    
    def process_media_data(self, json_file, output_base_dir, media_type='movies'):
        """معالجة ملف JSON للأفلام أو المسلسلات"""
        print(f"\n{'='*60}")
        print(f"🎬 بدء معالجة {media_type.upper()}")
        print(f"{'='*60}\n")
        
        # قراءة البيانات
        with open(json_file, 'r', encoding='utf-8') as f:
            media_data = json.load(f)
        
        total_items = len(media_data)
        print(f"📊 إجمالي العناصر: {total_items}\n")
        
        updated_data = []
        tasks = []
        
        # إنشاء المجلدات
        posters_dir = os.path.join(output_base_dir, media_type, 'posters')
        backdrops_dir = os.path.join(output_base_dir, media_type, 'backdrops')
        logos_dir = os.path.join(output_base_dir, media_type, 'logos')
        
        # تجهيز المهام
        for idx, item in enumerate(media_data, 1):
            title = item.get('title', f'item_{idx}')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:50]  # تحديد طول الاسم
            
            item_tasks = {
                'poster': (item.get('poster'), posters_dir, f"{idx}_{safe_title}_poster.webp"),
                'backdrop': (item.get('backdrop'), backdrops_dir, f"{idx}_{safe_title}_backdrop.webp"),
                'logo': (item.get('logo'), logos_dir, f"{idx}_{safe_title}_logo.webp")
            }
            
            tasks.append((idx, item, item_tasks))
        
        # معالجة متعددة الخيوط
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for idx, item, item_tasks in tasks:
                future_map = {}
                for img_type, (url, output_dir, filename) in item_tasks.items():
                    if url and url != 'None':
                        future = executor.submit(self.process_single_image, url, output_dir, filename)
                        future_map[future] = (idx, img_type, filename)
                        futures.append(future)
                
                # حفظ معلومات المهام
                item['_futures'] = future_map
            
            # انتظار النتائج
            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                
                if completed % 10 == 0:
                    print(f"\n📈 التقدم: {completed}/{len(futures)} ({(completed/len(futures)*100):.1f}%)\n")
        
        # تحديث البيانات بالمسارات الجديدة
        for idx, item, item_tasks in tasks:
            new_item = {
                'title': item['title'],
                'poster': None,
                'backdrop': None,
                'logo': None
            }
            
            for img_type, (url, output_dir, filename) in item_tasks.items():
                if url and url != 'None':
                    new_path = os.path.join(output_dir, filename)
                    if os.path.exists(new_path):
                        new_item[img_type] = new_path
            
            updated_data.append(new_item)
        
        # حفظ البيانات المحدثة
        output_json = json_file.replace('.json', '_webp.json')
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ تم حفظ البيانات المحدثة في: {output_json}")
        
        return updated_data
    
    def print_summary(self):
        """طباعة ملخص العملية"""
        print(f"\n{'='*60}")
        print("📊 ملخص العملية")
        print(f"{'='*60}")
        print(f"✓ نجح: {self.success_count} صورة")
        print(f"❌ فشل: {self.failed_count} صورة")
        print(f"📦 الحجم الأصلي: {self.total_original_size/1024/1024:.2f} ميجا")
        print(f"📦 الحجم الجديد: {self.total_converted_size/1024/1024:.2f} ميجا")
        
        if self.total_original_size > 0:
            saved = self.total_original_size - self.total_converted_size
            percentage = (saved / self.total_original_size) * 100
            print(f"💾 توفير: {saved/1024/1024:.2f} ميجا ({percentage:.1f}%)")
        print(f"{'='*60}\n")


def main():
    """البرنامج الرئيسي"""
    print("🎨 برنامج تحويل وضغط الصور إلى WebP")
    print("="*60)
    
    # الإعدادات
    converter = ImageConverter(
        quality=75,      # جودة 75% (ممتازة ومضغوطة)
        max_width=1920   # أقصى عرض 1920 بكسل
    )
    
    output_dir = "converted_images"
    
    # معالجة الأفلام
    if os.path.exists('movies_data.json'):
        print("\n🎬 معالجة الأفلام...")
        converter.process_media_data('movies_data.json', output_dir, 'movies')
    else:
        print("⚠️ ملف movies_data.json غير موجود")
    
    # معالجة المسلسلات
    if os.path.exists('series_data.json'):
        print("\n📺 معالجة المسلسلات...")
        converter.process_media_data('series_data.json', output_dir, 'series')
    else:
        print("⚠️ ملف series_data.json غير موجود")
    
    # طباعة الملخص النهائي
    converter.print_summary()
    
    print("✅ تمت العملية بنجاح!")
    print(f"📁 الصور المحفوظة في: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()