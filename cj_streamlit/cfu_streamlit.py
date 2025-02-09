import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import pandas as pd

def create_circular_mask(h, w, center, radius):
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)
    mask = dist_from_center <= radius
    return mask

def preprocess_image(image):
    # 그레이스케일 변환
    if len(image.shape) > 2:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
        
    # 가우시안 블러
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 배경 제거
    background = cv2.morphologyEx(blurred, cv2.MORPH_DILATE,
                                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    diff_img = cv2.absdiff(blurred, background)
    
    # 대비 향상
    norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, 
                           norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    
    return norm_img

def detect_colonies(image, min_dist=20, min_radius=3, max_radius=15, 
                   threshold=0.1, crop_region=None):
    if crop_region:
        x, y, w, h = crop_region
        image = image[y:y+h, x:x+w]
    
    # 이미지 전처리
    processed = preprocess_image(image)
    
    # Blob 검출
    params = cv2.SimpleBlobDetector_Params()
    params.minThreshold = 50
    params.maxThreshold = 200
    params.filterByArea = True
    params.minArea = np.pi * min_radius * min_radius
    params.maxArea = np.pi * max_radius * max_radius
    params.filterByCircularity = True
    params.minCircularity = 0.6
    params.filterByConvexity = True
    params.minConvexity = 0.8
    params.filterByInertia = True
    params.minInertiaRatio = 0.5
    params.minDistBetweenBlobs = min_dist

    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(processed)
    
    # 검출된 좌표 변환
    colonies = []
    for kp in keypoints:
        x, y = kp.pt
        r = kp.size / 2
        if crop_region:
            x += crop_region[0]
            y += crop_region[1]
        colonies.append((int(x), int(y), int(r)))
    
    return colonies

def draw_markers(image, markers, color=(255, 0, 0)):
    img_with_markers = image.copy()
    for i, (x, y, r) in enumerate(markers):
        # 원 그리기
        cv2.circle(img_with_markers, (x, y), r, color, 2)
        # 번호 표시
        cv2.putText(img_with_markers, str(i+1), (x-10, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return img_with_markers

def main():
    st.title("Colony Counter")
    st.write("박테리아 Colony 자동/수동 카운팅 도구")

    # 세션 상태 초기화
    if 'markers' not in st.session_state:
        st.session_state.markers = []
    if 'crop_region' not in st.session_state:
        st.session_state.crop_region = None
    if 'image' not in st.session_state:
        st.session_state.image = None
    if 'auto_detected' not in st.session_state:
        st.session_state.auto_detected = []

    # 이미지 업로드
    uploaded_file = st.file_uploader("이미지 파일을 선택하세요", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        # 이미지 로드
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if image is None:  # 이미지가 제대로 로드되지 않은 경우
            st.error("이미지를 로드할 수 없습니다. 올바른 파일 형식을 확인하세요.")
            return  # 함수 종료
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        st.session_state.image = image.copy()
        
        # 이미지 표시 추가
        st.image(st.session_state.image, use_column_width=True)  # 이미지 표시

        # 사이드바에 검출 파라미터 설정
        st.sidebar.header("검출 파라미터")
        min_dist = st.sidebar.slider("최소 거리", 10, 50, 20)
        min_radius = st.sidebar.slider("최소 반지름", 1, 10, 3)
        max_radius = st.sidebar.slider("최대 반지름", 5, 30, 15)
        threshold = st.sidebar.slider("임계값", 0.0, 1.0, 0.1)

        # 메인 기능 선택
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("영역 선택"):
                st.session_state.crop_region = None
                crop_coords = st.text_input(
                    "영역 좌표 입력 (x,y,width,height)",
                    help="예: 100,100,500,500"
                )
                if crop_coords:
                    try:
                        x, y, w, h = map(int, crop_coords.split(','))
                        st.session_state.crop_region = (x, y, w, h)
                    except:
                        st.error("올바른 좌표 형식이 아닙니다.")

        with col2:
            if st.button("자동 검출"):
                colonies = detect_colonies(
                    st.session_state.image,
                    min_dist,
                    min_radius,
                    max_radius,
                    threshold,
                    st.session_state.crop_region
                )
                st.session_state.auto_detected = colonies
                st.session_state.markers.extend(colonies)
                st.success(f"{len(colonies)}개의 Colony가 검출되었습니다!")

        with col3:
            if st.button("초기화"):
                st.session_state.markers = []
                st.session_state.auto_detected = []
                st.session_state.crop_region = None

        # 현재 상태 표시
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"자동 검출: {len(st.session_state.auto_detected)}개")
        with col2:
            st.write(f"총 마커: {len(st.session_state.markers)}개")

        # 마커 그리기
        display_image = st.session_state.image.copy()
        if st.session_state.crop_region:
            x, y, w, h = st.session_state.crop_region
            cv2.rectangle(display_image, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # 마커 그리기
        display_image = draw_markers(display_image, st.session_state.markers)
        st.image(display_image, use_column_width=True)

        # 마커 수동 추가/제거
        st.write("### 수동 마커 추가/제거")
        col1, col2 = st.columns(2)
        
        with col1:
            coords = st.text_input(
                "마커 추가 (x,y)",
                help="예: 100,100"
            )
            if coords:
                try:
                    x, y = map(int, coords.split(','))
                    st.session_state.markers.append((x, y, 5))  # 기본 반지름 5
                    st.experimental_rerun()
                except:
                    st.error("올바른 좌표 형식이 아닙니다.")

        with col2:
            marker_index = st.number_input(
                "제거할 마커 번호",
                min_value=1,
                max_value=len(st.session_state.markers) if st.session_state.markers else 1,
                help="마커 번호를 입력하세요"
            )
            if st.button("마커 제거"):
                if marker_index <= len(st.session_state.markers):
                    st.session_state.markers.pop(marker_index - 1)
                    st.experimental_rerun()

        # 결과 저장
        if st.button("결과 저장"):
            if st.session_state.markers:
                df = pd.DataFrame(st.session_state.markers, 
                                columns=['x', 'y', 'radius'])
                csv = df.to_csv(index=False)
                st.download_button(
                    "CSV 다운로드",
                    csv,
                    "colony_counts.csv",
                    "text/csv",
                    key='download-csv'
                )

if __name__ == "__main__":
    main()
