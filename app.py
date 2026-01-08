import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import zipfile
import os

# ==========================================
# [설정] API 키 관리 (멀티 플랫폼)
# ==========================================
UNSPLASH_ACCESS_KEY = "866tz8GXjPx2sjBhd9p58nNM5fyuBsk5LRyU8HPQfiU"
PEXELS_API_KEY = "dP09tHiW7RyniXLXnJdbV2aEpbAl86XYnYQZGoGo7Cpta9fFhPSJRDgp"
PIXABAY_API_KEY = "54085998-ef78c84d4ce4500e6d211c19d"

# ==========================================
# [설정] 디자인 상수
# ==========================================
ASSETS_DIR = "assets"
FONT_TITLE_NAME = "NotoSansKR-Bold.ttf"
FONT_BODY_NAME = "NotoSansKR-Medium.ttf"

CANvas_WIDTH = 1080
CANvas_HEIGHT = 1350
BRAND_COLOR = "#C2FF00" 

ALIGN_LEFT_X = 80 

# ==========================================
# [함수] 이미지 소스별 검색 로직 (통합)
# ==========================================
def search_unsplash(query, page=1):
    if "866tz" not in UNSPLASH_ACCESS_KEY and "여기에" in UNSPLASH_ACCESS_KEY:
        st.error("Unsplash API 키가 없습니다.")
        return []
    url = "https://api.unsplash.com/search/photos"
    params = {"query": query, "client_id": UNSPLASH_ACCESS_KEY, "per_page": 30, "page": page, "orientation": "portrait"}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return [{'id': item['id'], 'source': 'Unsplash', 'urls': {'thumb': item['urls']['thumb'], 'regular': item['urls']['regular']}} for item in res.json()['results']]
    except: pass
    return []

def search_pexels(query, page=1):
    if "여기에" in PEXELS_API_KEY:
        st.warning("Pexels API 키를 입력해야 검색됩니다.")
        return []
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 30, "page": page, "orientation": "portrait"}
    try:
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            return [{'id': item['id'], 'source': 'Pexels', 'urls': {'thumb': item['src']['tiny'], 'regular': item['src']['portrait']}} for item in res.json()['photos']]
    except: pass
    return []

def search_pixabay(query, page=1):
    if "여기에" in PIXABAY_API_KEY:
        st.warning("Pixabay API 키를 입력해야 검색됩니다.")
        return []
    url = "https://pixabay.com/api/"
    params = {"key": PIXABAY_API_KEY, "q": query, "per_page": 30, "page": page, "image_type": "photo", "orientation": "vertical"}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return [{'id': item['id'], 'source': 'Pixabay', 'urls': {'thumb': item['previewURL'], 'regular': item['largeImageURL']}} for item in res.json()['hits']]
    except: pass
    return []

# ==========================================
# [함수] 그리기 및 유틸리티
# ==========================================
def get_font(filename, size):
    try: return ImageFont.truetype(os.path.join(ASSETS_DIR, filename), size)
    except:
        try: return ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", size)
        except: return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    if not text: return []
    final_lines = []
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        if not paragraph.strip():
            final_lines.append("")
            continue
        words = paragraph.split()
        if not words:
            final_lines.append("")
            continue
        current_line = words[0]
        for word in words[1:]:
            bbox = draw.textbbox((0, 0), current_line + " " + word, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line += " " + word
            else:
                final_lines.append(current_line)
                current_line = word
        final_lines.append(current_line)
    return final_lines

def calculate_text_block_height(draw, title_lines, font_t, body_lines, font_b):
    total_h = 0
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=font_t)
        total_h += (bbox[3] - bbox[1]) + 20
    if body_lines:
        total_h += 30 
        for line in body_lines:
            bbox = draw.textbbox((0, 0), line, font=font_b)
            total_h += (bbox[3] - bbox[1]) + 15
    return total_h

def draw_dotted_line(draw, start, end, fill, width=2, gap=8, dash=2):
    x1, y1 = start
    x2, y2 = end
    total_len = x2 - x1
    if total_len <= 0: return
    current_x = x1
    while current_x < x2:
        draw.line([(current_x, y1), (min(current_x + dash, x2), y1)], fill=fill, width=width)
        current_x += (dash + gap)

def draw_embossed_text(draw, xy, text, font, fill_color="#FFFFFF"):
    x, y = xy
    draw.text((x+3, y+3), text, font=font, fill="#000000") 
    draw.text((x+1, y+1), text, font=font, fill="#333333") 
    draw.text((x, y), text, font=font, fill=fill_color)

def create_slide(data):
    bg_source = data.get('bg_source')
    layout = data.get('layout', '상단 정렬')
    title_color = data.get('title_color', '#FFFFFF')
    body_color = data.get('body_color', '#FFFFFF')
    category = data.get('category', '') 
    keyword = data.get('keyword', '') 
    
    # [설정] 사용자 지정 글씨 크기 가져오기
    custom_sub_size = data.get('sub_size', 45) # 표지 부제목 기본값 45
    custom_body_size = data.get('body_size', 40) # 내용 본문 기본값 40

    img = Image.new('RGB', (CANvas_WIDTH, CANvas_HEIGHT), "#1A1A1A")
    draw = ImageDraw.Draw(img)

    # 1. 배경 이미지 합성
    is_unsplash = False 
    try:
        bg_img = None
        if bg_source:
            if isinstance(bg_source, str) and bg_source.startswith('http'):
                res = requests.get(bg_source)
                bg_img = Image.open(BytesIO(res.content)).convert('RGB')
                if "images.unsplash.com" in bg_source: is_unsplash = True
            elif hasattr(bg_source, 'read'):
                bg_source.seek(0)
                bg_img = Image.open(bg_source).convert('RGB')
            elif isinstance(bg_source, Image.Image):
                bg_img = bg_source.convert('RGB')

            if bg_img:
                bg_ratio = bg_img.width / bg_img.height
                canvas_ratio = CANvas_WIDTH / CANvas_HEIGHT
                if bg_ratio > canvas_ratio:
                    new_h = CANvas_HEIGHT
                    new_w = int(new_h * bg_ratio)
                    offset_x, offset_y = (new_w - CANvas_WIDTH) // 2, 0
                else:
                    new_w = CANvas_WIDTH
                    new_h = int(new_w / bg_ratio)
                    offset_x, offset_y = 0, (new_h - CANvas_HEIGHT) // 2
                bg_img = bg_img.resize((new_w, new_h), Image.LANCZOS)
                img.paste(bg_img, (-offset_x, -offset_y))
                
                # 아웃트로가 아닐 때만 틴트
                if data.get('type') != 'outro':
                    dim = Image.new('RGBA', img.size, (0, 0, 0, 110))
                    img.paste(dim, (0,0), dim)
    except Exception as e: print(f"배경 에러: {e}")

    # 2. 저작권 표시 (Unsplash만)
    if is_unsplash:
        font_c = get_font(FONT_BODY_NAME, 20)
        credit_text = "Photo by Unsplash"
        bbox = draw.textbbox((0, 0), credit_text, font=font_c)
        draw.text((CANvas_WIDTH - bbox[2] - 30, 30), credit_text, font=font_c, fill="#AAAAAA")

    # 3. 텍스트 그리기 준비
    type = data.get('type', 'content')
    title = data.get('title', '')
    content = data.get('content', '')

    font_t_size = 90 if type == 'cover' else 60
    font_b_size = custom_sub_size if type == 'cover' else custom_body_size
    
    if type == 'outro': font_t_size, font_b_size = 80, 50

    font_t = get_font(FONT_TITLE_NAME, font_t_size)
    font_b = get_font(FONT_BODY_NAME, font_b_size)
    
    margin_x = ALIGN_LEFT_X 
    max_width = CANvas_WIDTH - (margin_x * 2)

    title_lines = wrap_text(title, font_t, max_width, draw)
    body_lines = wrap_text(content, font_b, max_width, draw)
    block_h = calculate_text_block_height(draw, title_lines, font_t, body_lines, font_b)
    
    start_y = 150 
    if layout == '중앙 정렬': start_y = (CANvas_HEIGHT - block_h) // 2
    elif layout == '하단 정렬': start_y = CANvas_HEIGHT - block_h - 250 

    current_y = start_y
    
    # [표지 전용] SYSO MAGAZINE 헤더
    if type == 'cover':
        header_y = start_y - 80 
        font_header = get_font(FONT_TITLE_NAME, 30)
        
        syso_text = "SYSO"
        syso_bbox = draw.textbbox((0,0), syso_text, font=font_header)
        syso_w, syso_h = syso_bbox[2] - syso_bbox[0], syso_bbox[3] - syso_bbox[1]
        
        box_padding_x, box_padding_y = 10, 5
        box_w = syso_w + (box_padding_x * 2)
        box_h = syso_h + (box_padding_y * 2) + 5
        box_x = ALIGN_LEFT_X 
        
        bg_patch = img.crop((int(box_x), int(header_y), int(box_x + box_w), int(header_y + box_h)))
        mask = Image.new("L", bg_patch.size, 0)
        d_mask = ImageDraw.Draw(mask)
        d_mask.text((box_padding_x, box_padding_y - 2), syso_text, font=font_header, fill=255)
        
        draw.rectangle([(box_x, header_y), (box_x + box_w, header_y + box_h)], fill=BRAND_COLOR)
        img.paste(bg_patch, (int(box_x), int(header_y)), mask)
        
        mag_text = "MAGAZINE"
        draw.text((box_x + box_w + 10, header_y + box_padding_y - 2), mag_text, font=font_header, fill=BRAND_COLOR)

    # 텍스트 출력 로직
    if type == 'cover': # 양각
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=font_t)
            draw_embossed_text(draw, (margin_x, current_y), line, font=font_t, fill_color=title_color)
            current_y += (bbox[3] - bbox[1]) + 20
        
        # [수정] 표지 제목과 부제목 사이 간격 늘림 (20 -> 60)
        current_y += 60 
        
        for line in body_lines:
            bbox = draw.textbbox((0, 0), line, font=font_b)
            draw_embossed_text(draw, (margin_x, current_y), line, font=font_b, fill_color=body_color)
            current_y += (bbox[3] - bbox[1]) + 15
            
    elif type == 'outro':
        # [수정] 아웃트로 전용 로직: BALANCE YOUR (KEYWORD) + 중앙 정렬 + 에러 해결
        
        # 1. 아웃트로 메인 텍스트 처리
        full_title = title.strip()
        prefix = "BALANCE YOUR"
        
        if prefix in full_title:
            remainder = full_title.replace(prefix, "").strip()
            w_prefix = draw.textlength(prefix, font=font_t)
            w_space = draw.textlength(" ", font=font_t)
            w_remain = draw.textlength(remainder, font=font_t)
            total_w = w_prefix + w_space + w_remain
            
            start_x = (CANvas_WIDTH - total_w) / 2
            outro_y = (CANvas_HEIGHT - (font_t_size + 30 + font_b_size)) / 2 - 50

            draw.text((start_x, outro_y), prefix, font=font_t, fill="#FFFFFF") 
            draw.text((start_x + w_prefix + w_space, outro_y), remainder, font=font_t, fill=BRAND_COLOR) 
            current_y = outro_y + font_t_size + 30
        else:
            w_title = draw.textlength(full_title, font=font_t)
            start_x = (CANvas_WIDTH - w_title) / 2
            outro_y = (CANvas_HEIGHT - (font_t_size + 30 + font_b_size)) // 2 - 50
            draw.text((start_x, outro_y), full_title, font=font_t, fill="#FFFFFF")
            current_y = outro_y + font_t_size + 30

        # 2. 아웃트로 부제목 (에러 수정: 여러 줄 처리)
        if content:
            # 부제목도 wrap_text를 사용하여 여러 줄로 나눔
            outro_lines = wrap_text(content, font_b, CANvas_WIDTH - 200, draw)
            
            for line in outro_lines:
                w_line = draw.textlength(line, font=font_b)
                start_x_line = (CANvas_WIDTH - w_line) / 2
                draw.text((start_x_line, current_y), line, font=font_b, fill="#DDDDDD")
                
                # 다음 줄 위치 계산
                bbox = draw.textbbox((0, 0), line, font=font_b)
                current_y += (bbox[3] - bbox[1]) + 15

    else: # 일반 내용 페이지
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=font_t)
            draw.text((margin_x, current_y), line, font=font_t, fill=title_color)
            current_y += (bbox[3] - bbox[1]) + 20
        if body_lines:
            current_y += 30 
            for line in body_lines:
                bbox = draw.textbbox((0, 0), line, font=font_b)
                draw.text((margin_x, current_y), line, font=font_b, fill=body_color)
                current_y += (bbox[3] - bbox[1]) + 15

    # 4. 공통 로고 및 하단 (모든 페이지 중앙 하단)
    try:
        logo = Image.open(os.path.join(ASSETS_DIR, "logo.png")).convert("RGBA")
        logo.thumbnail((80, 80))
        logo_x = (CANvas_WIDTH - logo.width) // 2
        logo_y = CANvas_HEIGHT - 100 
        img.paste(logo, (logo_x, logo_y), logo)
        
        # [표지 전용] 하단 디자인
        if type == 'cover':
            font_footer = get_font(FONT_TITLE_NAME, 26)
            footer_text_y = logo_y + 25
            
            if category:
                draw.text((ALIGN_LEFT_X, footer_text_y), category, font=font_footer, fill=title_color, anchor="lm")
            
            if keyword:
                kw_text = f"#{keyword}" if not keyword.startswith("#") else keyword
                right_margin = ALIGN_LEFT_X
                draw.text((CANvas_WIDTH - right_margin, footer_text_y), kw_text, font=font_footer, fill=title_color, anchor="rm")
                     
    except Exception as e: print(f"로고/푸터 에러: {e}")

    return img

# ==========================================
# [UI] 화면 구성
# ==========================================
st.set_page_config(layout="wide", page_title="인스타 매거진 Final")

if 'gallery_images' not in st.session_state: st.session_state['gallery_images'] = [] # 통합 갤러리
if 'slide_configs' not in st.session_state: st.session_state['slide_configs'] = {}
if 'search_page' not in st.session_state: st.session_state['search_page'] = 1 

st.title("🎨 Instagram Magazine Maker (for SYSO)")

# --- 1. 통합 갤러리 ---
with st.expander("🖼️ 이미지 갤러리 (멀티 소스 & 업로드)", expanded=True):
    c1, c2 = st.columns([1, 1])
    
    # A. 멀티 소스 검색
    with c1:
        st.subheader("1. 이미지 검색")
        source_type = st.radio("검색 소스", ["Unsplash", "Pexels", "Pixabay"], horizontal=True)
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        query = col_s1.text_input("검색어 (영문)", value="aesthetic")
        
        if col_s2.button("검색"):
            st.session_state['search_page'] = 1 
            results = []
            if source_type == "Unsplash": results = search_unsplash(query, 1)
            elif source_type == "Pexels": results = search_pexels(query, 1)
            elif source_type == "Pixabay": results = search_pixabay(query, 1)
            
            if results: st.session_state['search_temp'] = results
            else: st.warning("검색 결과가 없거나 API 키를 확인해주세요.")
        
        if col_s3.button("더보기"):
            st.session_state['search_page'] += 1
            new_results = []
            if source_type == "Unsplash": new_results = search_unsplash(query, st.session_state['search_page'])
            elif source_type == "Pexels": new_results = search_pexels(query, st.session_state['search_page'])
            elif source_type == "Pixabay": new_results = search_pixabay(query, st.session_state['search_page'])

            if new_results:
                if 'search_temp' not in st.session_state: st.session_state['search_temp'] = []
                st.session_state['search_temp'].extend(new_results) 
                st.success(f"{len(new_results)}장 추가됨")
        
        if 'search_temp' in st.session_state:
            st.caption(f"검색 결과 ({source_type})")
            scols = st.columns(4)
            for i, img in enumerate(st.session_state['search_temp']):
                with scols[i % 4]:
                    st.image(img['urls']['thumb'], use_container_width=True)
                    exists = any(x['id'] == img['id'] for x in st.session_state['gallery_images'])
                    if not exists:
                        if st.button("담기", key=f"add_{img['id']}"):
                            st.session_state['gallery_images'].append(img)
                            st.rerun()
                    else:
                        st.button("✅", key=f"done_{img['id']}", disabled=True)

    # B. 업로드
    with c2:
        st.subheader("2. 내 이미지 업로드")
        uploaded_files = st.file_uploader("이미지 파일 선택", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if uploaded_files:
            for uf in uploaded_files:
                if not any(x.get('name') == uf.name for x in st.session_state['gallery_images']):
                    img_obj = Image.open(uf)
                    st.session_state['gallery_images'].append({
                        'id': uf.name, 
                        'source': 'Upload', 
                        'urls': {'thumb': img_obj, 'regular': uf}, 
                        'name': uf.name,
                        'obj': img_obj
                    })
            
    # C. 장바구니 현황
    st.markdown("---")
    st.subheader(f"🛒 사용 가능한 이미지 목록")
    if not st.session_state['gallery_images']:
        st.info("이미지가 없습니다.")
    else:
        g_cols = st.columns(8)
        for idx, img in enumerate(st.session_state['gallery_images']):
            with g_cols[idx % 8]:
                thumb = img['urls']['thumb']
                if isinstance(thumb, str): st.image(thumb, caption=img['source'])
                else: st.image(thumb, caption="내 사진")
                
                if st.button("❌ 삭제", key=f"del_{img['id']}_{idx}"):
                    st.session_state['gallery_images'].pop(idx)
                    st.rerun()

# --- 2. 편집 ---
st.markdown("---")
st.header("📝 슬라이드 편집")
st.caption("💡 모든 텍스트는 좌측 기준선에 맞춰 깔끔하게 정렬됩니다.")

num_pages = st.number_input("내용 페이지 수", min_value=1, value=3)
total_pages = 1 + num_pages + 1
tabs = st.tabs(["표지"] + [f"내용 {i+1}" for i in range(num_pages)] + ["아웃트로"])

bg_options = {"선택 안 함": None}
for i, img in enumerate(st.session_state['gallery_images']):
    label = f"[{img['source']}] 이미지 {i+1}" if img['source'] != 'Upload' else f"[내 사진] {img['name']}"
    bg_options[label] = img['urls']['regular']

def editor_ui(key):
    c1, c2, c3 = st.columns(3)
    with c1: layout = st.selectbox("레이아웃", ["상단 정렬", "중앙 정렬", "하단 정렬"], key=f"lo_{key}")
    with c2: t_col = st.color_picker("제목 색상", "#FFFFFF", key=f"tc_{key}")
    with c3: b_col = st.color_picker("본문 색상", "#FFFFFF", key=f"bc_{key}")
    st.write("배경 이미지 선택:")
    bg_key = st.selectbox("갤러리에서 선택", list(bg_options.keys()), key=f"bg_{key}")
    return layout, t_col, b_col, bg_options[bg_key]

# (1) 표지
with tabs[0]:
    category = st.selectbox("주제 (Category)", ["DAY BALANCE", "NIGHT BALANCE", "LIVE BALANCE"], key="cat_cover")
    keyword = st.text_input("하단 키워드 (예: 붓기)", key="kw_cover")
    
    t = st.text_area("표지 제목", "제목을\n입력하세요", height=100, key="t_cover")
    c = st.text_area("표지 부제목", "부제목을 입력하세요", height=70, key="c_cover")
    
    # [수정] 부제목 글씨 크기 조절 슬라이더
    sub_size = st.slider("부제목 크기", min_value=30, max_value=80, value=45, key="sub_size_cover")
    
    layout, t_col, b_col, bg = editor_ui("cover")
    st.session_state['slide_configs'][0] = {
        "type": "cover", "title": t, "content": c, "category": category, "keyword": keyword,
        "bg_source": bg, "layout": layout, "title_color": t_col, "body_color": b_col,
        "sub_size": sub_size 
    }

# (2) 내용
for i in range(num_pages):
    with tabs[i+1]:
        t = st.text_area(f"소제목 {i+1}", key=f"tt_{i}", height=70)
        c = st.text_area(f"본문 {i+1}", key=f"cc_{i}", height=150)
        
        # [수정] 본문 글씨 크기 조절 슬라이더
        body_size = st.slider(f"본문 크기 {i+1}", min_value=20, max_value=80, value=40, key=f"bs_{i}")

        layout, t_col, b_col, bg = editor_ui(f"cont_{i}")
        st.session_state['slide_configs'][i+1] = {
            "type": "content", "title": t, "content": c, "bg_source": bg, 
            "layout": layout, "title_color": t_col, "body_color": b_col,
            "body_size": body_size 
        }

# (3) 아웃트로
with tabs[-1]:
    t = st.text_area("마지막 큰 문구", "BALANCE YOUR (LIFE)", height=70, key="t_outro")
    c = st.text_area("마지막 작은 문구 (부제목)", "팔로우 부탁드려요!", height=70, key="c_outro")
    
    st.caption("💡 'BALANCE YOUR' 뒤에 오는 단어는 자동으로 브랜드 컬러(#C2FF00)가 적용됩니다.")
    st.caption("💡 배경 이미지는 원본 밝기 그대로 적용됩니다.")
    
    layout, t_col, b_col, bg = editor_ui("outro")
    st.session_state['slide_configs'][total_pages-1] = {"type": "outro", "title": t, "content": c, "bg_source": bg, "layout": layout, "title_color": t_col, "body_color": b_col}

# --- 3. 생성 ---
st.markdown("---")
if st.button("✨ 이미지 생성 및 다운로드"):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        cols = st.columns(min(total_pages, 6))
        for i in range(total_pages):
            conf = st.session_state['slide_configs'].get(i)
            if conf:
                img = create_slide(conf)
                with cols[i % 6]: st.image(img, caption=f"P.{i+1}", use_container_width=True)
                buf = BytesIO()
                img.save(buf, format='JPEG', quality=95)
                zf.writestr(f"slide_{i+1:02d}.jpg", buf.getvalue())
                
    st.success("완료!")
    st.download_button("📦 ZIP 다운로드", zip_buffer.getvalue(), "magazine.zip", "application/zip")