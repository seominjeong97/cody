"""색 조합 코디 공방
실행: streamlit run style_app.py
GitHub에 이 파일과 requirements.txt 업로드 → Streamlit Community Cloud에서 배포.
별도 데이터/로그인/AI/DB 설정 불필요. 카메라는 사진의 대표 색 추출용. QR 공유는 배포 주소를 QR로 변환하여 사용.
작업/컬렉션은 세션에만 보관되므로 종료/새로고침 전에 JSON 백업을 다운로드하세요.
JSON 가져오기로 복원 가능합니다. PNG는 도형 기반 스타일 보드이며 실제 착장/핏이 아닙니다.
"""
import colorsys
import copy
import io
import json
import random
import re
import uuid
from datetime import datetime

import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(page_title='색 조합 코디 공방',page_icon='🎨',layout='centered')
COLORS={'크림':'#F4EBDD','라벤더':'#B8A4CC','핑크':'#DCA7AF','민트':'#A6C4B5','하늘':'#9CBAD2','버터':'#E7CE83','네이비':'#344963','브라운':'#785849','차콜':'#434449','화이트':'#FAFAF7','진청':'#3D5773','코랄':'#D68673'}
ITEMS={'상의':['티셔츠','셔츠','니트','후드'],'하의':['바지','반바지','스커트'],'신발':['스니커즈','로퍼','부츠','샌들','플랫슈즈','하이힐','슬리퍼'],'가방':['숄더백','토트백','백팩','크로스백','클러치','버킷백']}
PRESETS={'산뜻한 나들이':['#F4EBDD','#3D5773','#FAFAF7','#785849'],'라벤더 오후':['#B8A4CC','#F4EBDD','#434449','#DCA7AF'],'차분한 모노톤':['#FAFAF7','#434449','#434449','#9A9A9A'],'버터와 민트':['#E7CE83','#A6C4B5','#F4EBDD','#785849']}
MODES=['뉴트럴 + 포인트','톤온톤','유사색','보색 포인트','모노톤','자유 조합']

def default():
 return {'items':{k:ITEMS[k][0] for k in ITEMS},'colors':dict(zip(ITEMS,PRESETS['산뜻한 나들이'])),'locks':{k:False for k in ITEMS},'background':'#F2F1EE'}
def valid_board(b):
 if not isinstance(b,dict): raise ValueError('보드 형식 오류')
 for k in ITEMS:
  if b['items'][k] not in ITEMS[k] or not re.fullmatch(r'#[0-9a-fA-F]{6}',b['colors'][k]) or type(b['locks'][k]) is not bool: raise ValueError('아이템/색상 오류')
 if not re.fullmatch(r'#[0-9a-fA-F]{6}',b['background']): raise ValueError('배경 오류')
 return {key:{k:b[key][k] for k in ITEMS} for key in ['items','colors','locks']}|{'background':b['background']}
def commit(board):
 valid_board(board)
 if board!=st.session_state.board:
  st.session_state.undo=(st.session_state.undo+[copy.deepcopy(st.session_state.board)])[-40:]
  st.session_state.redo=[];st.session_state.board=copy.deepcopy(board)
def rgb(hexcode): return tuple(int(hexcode[i:i+2],16) for i in (1,3,5))
def hexrgb(v): return '#'+''.join(f'{round(max(0,min(1,x))*255):02X}' for x in v)
def generate(board,mode):
 b=copy.deepcopy(board);h=random.random()
 for i,k in enumerate(ITEMS):
  if b['locks'][k]: continue
  if mode=='모노톤': color=hexrgb((lambda v:(v,v,v))(random.choice([.18,.4,.7,.94])))
  elif mode=='자유 조합': color=random.choice(list(COLORS.values()))
  elif mode=='뉴트럴 + 포인트': color=hexrgb(colorsys.hsv_to_rgb(h,.38,.82)) if i==3 else random.choice(['#F4EBDD','#434449','#785849','#FAFAF7'])
  elif mode=='보색 포인트': color=hexrgb(colorsys.hsv_to_rgb((h+(.5 if i==3 else 0))%1,.3 if i<3 else .6,random.uniform(.5,.92)))
  else: color=hexrgb(colorsys.hsv_to_rgb((h+(i*.045 if mode=='유사색' else 0))%1,random.uniform(.18,.45),random.uniform(.5,.95)))
  b['colors'][k]=color
 return b

def render(board):
 im=Image.new('RGB',(720,800),board['background']);d=ImageDraw.Draw(im)
 # 정면 인체 합성이 아닌, 내장 도형의 플랫레이 보드.
 top=board['items']['상의'];c=board['colors']['상의'];edge='#4F5055'
 pts=[(210,85),(265,58),(310,78),(355,58),(410,85),(447,170),(405,189),(382,146),(382,310),(238,310),(238,146),(215,189),(173,170)]
 d.polygon(pts,fill=c,outline=edge,width=3)
 d.arc((265,51,355,115),0,180,fill=edge,width=3)
 if top=='셔츠':
  d.line([(310,105),(310,305)],fill=edge,width=2)
  d.polygon([(265,63),(310,104),(279,127)],outline=edge)
  d.polygon([(355,63),(310,104),(341,127)],outline=edge)
  for y in [150,190,230,270]:d.ellipse((305,y,311,y+6),fill=edge)
 elif top=='후드':
  d.arc((263,62,357,145),180,360,fill=edge,width=3)
  d.rounded_rectangle((265,224,355,275),radius=12,outline=edge,width=2)
 elif top=='니트':
  for x in range(248,380,12):d.line((x,150,x,295),fill=tuple(int(v*.88) for v in rgb(c)),width=2)
 else:
  d.line((238,150,238,178),fill=edge,width=2);d.line((382,150,382,178),fill=edge,width=2)
 bottom=board['items']['하의'];c=board['colors']['하의']
 if bottom=='스커트':d.polygon([(240,355),(380,355),(421,596),(199,596)],fill=c,outline=edge,width=3)
 else:
  end=535 if bottom=='반바지' else 665
  d.polygon([(230,355),(390,355),(410,end),(325,end),(310,443),(295,end),(210,end)],fill=c,outline=edge,width=3)
 d.line((235,375,385,375),fill=edge,width=2)
 c=board['colors']['가방'];bag=board['items']['가방']
 d.arc((495,220,610,350),180,360,fill=edge,width=9)
 d.rounded_rectangle((473,285,635,440),radius=12 if bag=='토트백' else 40,fill=c,outline=edge,width=3)
 if bag in ['숄더백','크로스백']:d.line((485,331,623,331),fill=edge,width=2)
 if bag=='백팩':
  d.rounded_rectangle((503,350,605,420),radius=12,outline=edge,width=3)
  d.line((480,300,458,430),fill=edge,width=5);d.line((630,300,648,430),fill=edge,width=5)
 if bag=='클러치':
  d.rectangle((465,210,645,355),fill=board['background'])
  d.polygon([(475,355),(630,355),(552,402)],outline=edge,width=3)
 if bag=='버킷백':
  d.line((485,308,620,308),fill=edge,width=3)
  d.line((540,308,525,375),fill=edge,width=3)
 if bag=='크로스백':d.line((470,220,640,400),fill=edge,width=5)
 shoe=board['items']['신발'];c=board['colors']['신발']
 for x in [464,572]:
  if shoe=='부츠':
   d.rectangle((x,520,x+52,620),fill=c,outline=edge,width=3)
   d.rounded_rectangle((x,590,x+85,650),radius=14,fill=c,outline=edge,width=3)
  else:
   d.rounded_rectangle((x,560,x+77,635),radius=25,fill=c,outline=edge,width=3)
   if shoe=='스니커즈':
    for y in [580,591,602]: d.line((x+17,y,x+55,y),fill=edge,width=2)
   elif shoe=='로퍼':d.line((x+10,590,x+65,590),fill=edge,width=3)
   elif shoe in ['샌들','슬리퍼']:
    d.rounded_rectangle((x+9,567,x+68,602),radius=17,fill=board['background'])
    d.line((x+5,607,x+70,607),fill=edge,width=5)
    if shoe=='샌들':d.line((x+5,580,x+70,580),fill=edge,width=5)
   elif shoe in ['플랫슈즈','하이힐']:
    d.ellipse((x+12,567,x+64,608),fill=board['background'],outline=edge,width=2)
    if shoe=='하이힐':d.rectangle((x+5,630,x+16,660),fill=c,outline=edge)
  d.line((x,635 if shoe!='부츠' else 650,x+77,635 if shoe!='부츠' else 650),fill=edge,width=5)
 for i,k in enumerate(ITEMS):
  x=200+i*85;d.ellipse((x,720,x+45,765),fill=board['colors'][k],outline=edge,width=2)
 return im

def png(board):
 b=io.BytesIO();render(board).save(b,format='PNG');return b.getvalue()

def save_copy(name,tag):
 st.session_state.collection.append({'id':str(uuid.uuid4()),'name':name.strip() or '이름 없는 코디','tag':tag,'favorite':False,'board':copy.deepcopy(st.session_state.board)})

for k,v in {'board':default(),'undo':[],'redo':[],'collection':[],'compare':[],'revision':0}.items():
 if k not in st.session_state:st.session_state[k]=v
st.markdown('''<style>
#MainMenu,footer{display:none}.block-container{max-width:1080px;padding-top:.8rem;padding-bottom:.5rem}
[data-testid="stAppViewContainer"]{background:#FCF9F5;color:#39333E}
[data-testid="stSidebar"]{background:#F1E8F1}
h1{font-size:1.65rem!important}h2,h3{font-size:1.15rem!important}
[data-testid="stVerticalBlock"]{gap:.45rem}
.stButton button,.stDownloadButton button{border-radius:12px;min-height:36px}
button[kind="primary"],button[kind="primaryFormSubmit"]{background:#CA3E50!important;color:white!important;border:0!important;width:auto!important}
[data-baseweb="select"]>div{border-radius:16px!important;background:#F6EEF5!important;border:1px solid #E6DAE6!important}
[data-testid="stForm"]{border:0;padding:.3rem}
@media(min-width:768px){[data-testid="stMainBlockContainer"]{padding-top:.6rem} }
</style>''',unsafe_allow_html=True)
with st.sidebar:
 st.title('🎀 코디 공방')
 page=st.radio('공간 이동',['홈','작업실','비교실','컬렉션','카메라','백업'],label_visibility='collapsed')
 st.caption('색을 고르고, 나만의 조합을 만들어요.')
 st.caption('작업은 세션에 보관돼요. 종료 전 백업해주세요.')

def preset_change():
 new=default();new['colors']=dict(zip(ITEMS,PRESETS[st.session_state.preset]));commit(new);st.session_state.revision+=1

b=st.session_state.board
st.title('색 조합 코디 공방')
if page=='홈':
 st.subheader('오늘의 스타일을 만들어볼까요? 🌷')
 left,right=st.columns([1,1])
 with left:
  st.write('옷 사진이나 자료 없이 바로 시작하세요.')
  st.selectbox('준비된 스타일',list(PRESETS),key='preset',on_change=preset_change)
  st.caption('선택하면 오른쪽 코디에 바로 반영돼요.')
  st.info('왼쪽 메뉴의 작업실에서 옷과 색을 바꿀 수 있어요. 카메라에서는 사진의 색을 가져올 수 있어요.')
  st.write(f'저장한 코디 **{len(st.session_state.collection)}개**')
 with right:st.image(render(st.session_state.board).resize((333,370)),width=333)
elif page=='작업실':
 left,right=st.columns([1,1])
 with left:st.image(render(b).resize((360,400)),width=360)
 with right:
  st.subheader('아이템과 색상')
  with st.form('edit_'+str(st.session_state.revision)):
   new=copy.deepcopy(b)
   for k in ITEMS:
    a,c=st.columns([3,1])
    new['items'][k]=a.selectbox(k,ITEMS[k],index=ITEMS[k].index(b['items'][k]))
    new['colors'][k]=c.color_picker(k+' 색',b['colors'][k])
   if st.form_submit_button('편집 적용',type='primary',use_container_width=False):
    commit(new);st.session_state.revision+=1;st.rerun()
  a,c=st.columns(2)
  if a.button('비교에 추가'):
   if len(st.session_state.compare)<3:st.session_state.compare.append(copy.deepcopy(b));st.toast('비교실에 추가했어요.')
   else:st.toast('비교실에서 후보를 먼저 삭제해주세요.')
  if c.button('컬렉션에 저장'):
   save_copy('코디 '+str(len(st.session_state.collection)+1),'일상');st.toast('저장했어요.')
  st.caption('색 선택 후 편집 적용을 눌러주세요.')
elif page=='비교실':
 if not st.session_state.compare:st.info('작업실에서 비교할 코디를 추가하세요.')
 else:
  for i,col in enumerate(st.columns(len(st.session_state.compare))):
   with col:
    st.image(render(st.session_state.compare[i]).resize((270,300)),caption=f'후보 {i+1}')
    if st.button('작업실로 불러오기',key='take'+str(i)):
     commit(st.session_state.compare[i]);st.session_state.revision+=1;st.toast('작업실에 반영했어요.')
    if st.button('후보 삭제',key='remove'+str(i)):st.session_state.compare.pop(i);st.rerun()
elif page=='컬렉션':
 if not st.session_state.collection:st.info('작업실에서 코디를 저장해보세요.')
 else:
  names=[f'{i+1}. {x["name"]}' for i,x in enumerate(st.session_state.collection)]
  index=st.selectbox('저장한 코디',range(len(names)),format_func=lambda i:names[i]);x=st.session_state.collection[index]
  a,c=st.columns(2)
  with a:st.image(render(x['board']).resize((315,350)),width=315)
  with c:
   name=st.text_input('이름',x['name'],max_chars=80,key='name'+x['id'])
   if st.button('이름 변경'):x['name']=name.strip() or '나의 코디';st.rerun()
   if st.button('작업실로 불러오기'):
    commit(x['board']);st.session_state.revision+=1;st.toast('작업실에 반영했어요.')
   st.download_button('코디 이미지 받기',png(x['board']),'style_board.png','image/png')
   confirm=st.checkbox('이 코디 삭제 확인')
   if st.button('삭제',disabled=not confirm):st.session_state.collection.pop(index);st.rerun()
elif page=='카메라':
 st.subheader('📷 사진에서 마음에 드는 색 가져오기')
 st.caption('가상 피팅이 아닌 색 추출 기능이에요. 카메라 허용이 필요하며 사진은 장기 저장하지 않아요.')
 a,c=st.columns(2)
 with a:
  source=st.radio('사진 선택 방법',['카메라 촬영','사진 업로드'],horizontal=True)
  photo=st.camera_input('사진 촬영') if source=='카메라 촬영' else st.file_uploader('사진 선택',type=['jpg','jpeg','png','webp'])
 with c:
  if photo:
   try:
    if photo.size>12000000:raise ValueError('12MB 이하 사진을 사용해주세요.')
    image=Image.open(photo)
    if image.width*image.height>25000000:raise ValueError('사진 해상도가 너무 커요. 축소해서 올려주세요.')
    from PIL import ImageOps
    image=ImageOps.exif_transpose(image).convert('RGB');image.thumbnail((400,400))
    quant=image.quantize(colors=6);palette=quant.getpalette();counts=sorted(quant.getcolors(),reverse=True)
    shades=['#'+''.join(f'{n:02X}' for n in palette[i*3:i*3+3]) for count,i in counts]
    st.image(image,width=230)
    color=st.selectbox('추출한 대표 색',shades)
    st.color_picker('선택한 색 미리보기',color,disabled=True)
    target=st.selectbox('적용할 아이템',list(ITEMS))
    if st.button('이 색 적용',type='primary'):
     new=copy.deepcopy(b);new['colors'][target]=color;commit(new);st.session_state.revision+=1;st.success('작업실에 반영했어요.')
   except Exception:st.error('사진을 읽지 못했어요. 12MB 이하 일반 사진으로 다시 시도해주세요.')
  else:st.info('옷이나 사물의 사진을 찍으면 대표 색 6개를 찾아드려요. 배경 색도 포함될 수 있어요.')
else:
 st.subheader('작업 백업과 복원')
 st.warning('새로고침·세션 종료 시 작업이 사라질 수 있어요. JSON 파일로 보관하세요.')
 backup={'schema':1,'board':b,'collection':st.session_state.collection}
 st.download_button('전체 작업 백업',json.dumps(backup,ensure_ascii=False,indent=2).encode(),'style_backup.json','application/json')
 uploaded=st.file_uploader('백업 파일 선택',type=['json'])
 confirm=st.checkbox('현재 작업과 컬렉션을 백업 내용으로 교체합니다.')
 if st.button('백업 복원',disabled=uploaded is None or not confirm):
  try:
   if uploaded.size>2000000:raise ValueError()
   data=json.loads(uploaded.getvalue())
   if data.get('schema')!=1 or not isinstance(data['collection'],list) or len(data['collection'])>500:raise ValueError()
   board=valid_board(data['board']);clean=[]
   for x in data['collection']:
    if not isinstance(x['name'],str) or len(x['name'])>80:raise ValueError()
    clean.append({'id':str(uuid.uuid4()),'name':x['name'],'tag':'일상','favorite':False,'board':valid_board(x['board'])})
   st.session_state.board=board;st.session_state.collection=clean;st.session_state.compare=[];st.session_state.undo=[];st.session_state.redo=[];st.session_state.revision+=1;st.success('복원했어요.')
  except Exception:st.error('유효한 앱 백업 파일을 선택해주세요. 기존 작업은 유지돼요.')
 st.caption('화면 속 색과 실제 원단의 색은 다를 수 있어요. 사진의 대표 색 추출은 퍼스널컬러 분석이나 착장 합성이 아닙니다.')
