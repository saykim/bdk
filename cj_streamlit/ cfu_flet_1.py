import flet as ft
from PIL import Image
import io
import base64

class ImageClickCounter:
    def __init__(self):
        self.click_count = 0
        self.clicks = []
        
    def main(self, page: ft.Page):
        page.title = "이미지 클릭 카운터"
        page.padding = 20
        
        def pick_files_result(e: ft.FilePickerResultEvent):
            if e.files:
                # 선택된 첫 번째 파일 처리
                file_path = e.files[0].path
                
                try:
                    # 이미지 로드 및 크기 조정
                    image = Image.open(file_path)
                    # 이미지 크기를 적절히 조정 (예: 최대 너비 800px)
                    max_width = 800
                    if image.size[0] > max_width:
                        ratio = max_width / image.size[0]
                        new_size = (max_width, int(image.size[1] * ratio))
                        image = image.resize(new_size)
                    
                    # 이미지를 bytes로 변환
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format or 'PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # base64로 인코딩
                    base64_image = base64.b64encode(img_byte_arr).decode()
                    
                    # 이미지 표시 업데이트
                    img_container.content = ft.Image(
                        src_base64=base64_image,
                        width=image.size[0],
                        height=image.size[1],
                        fit=ft.ImageFit.CONTAIN
                    )
                    
                    # Stack 컨테이너 크기 업데이트
                    stack.width = image.size[0]
                    stack.height = image.size[1]
                    
                    canvas.width = image.size[0]
                    canvas.height = image.size[1]
                    
                    page.update()
                except Exception as ex:
                    print(f"이미지 처리 중 오류 발생: {str(ex)}")

        def on_canvas_tap(e: ft.TapEvent):
            # 클릭 위치에 원 추가
            x, y = e.local_x, e.local_y
            circle = ft.Circle(
                x=x,
                y=y,
                radius=5,
                fill_color=ft.colors.RED_500,
                opacity=0.5
            )
            canvas.shapes.append(circle)
            self.clicks.append((x, y))
            self.click_count += 1
            
            # 클릭 카운트 업데이트
            count_text.value = f"클릭 횟수: {self.click_count}"
            page.update()

        def clear_canvas(e):
            canvas.shapes.clear()
            self.clicks.clear()
            self.click_count = 0
            count_text.value = f"클릭 횟수: {self.click_count}"
            page.update()

        # 파일 선택기
        pick_files_dialog = ft.FilePicker(
            on_result=pick_files_result
            # allow_multiple 인자 제거
        )
        
        # 파일 타입 필터 설정
        pick_files_dialog.file_type = ft.FilePickerFileType.IMAGE  # 이미지 파일만 선택 가능
        
        page.overlay.append(pick_files_dialog)
        
        # 이미지 컨테이너
        img_container = ft.Container(
            content=ft.Text("이미지를 선택해주세요"),
            alignment=ft.alignment.center
        )
        
        # 캔버스 (원을 그리기 위한)
        canvas = ft.Canvas(
            shapes=[],
            on_tap=on_canvas_tap
        )
        
        # Stack으로 이미지와 캔버스 겹치기
        stack = ft.Stack([
            img_container,
            canvas
        ])
        
        # 클릭 카운트 텍스트
        count_text = ft.Text(f"클릭 횟수: {self.click_count}", size=20)
        
        # 초기화 버튼
        clear_button = ft.ElevatedButton("초기화", on_click=clear_canvas)
        
        # 레이아웃
        page.add(
            ft.ElevatedButton(
                "이미지 선택",
                icon=ft.icons.UPLOAD_FILE,
                on_click=lambda _: pick_files_dialog.pick_files()
            ),
            stack,
            ft.Row([
                count_text,
                clear_button
            ])
        )

def main():
    app = ImageClickCounter()
    ft.app(target=app.main)

if __name__ == "__main__":
    main()
