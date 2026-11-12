"""색 조합 코디 공방
실행: streamlit run style_app.py
GitHub에 이 파일과 requirements.txt 업로드 → Streamlit Community Cloud에서 배포.
별도 데이터/로그인/AI/DB 설정 불필요. QR 공유는 배포 주소를 QR로 변환하여 사용.
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
ITEMS={'상의':['티셔츠','셔츠','니트','후드'],'하의':['바지','반바지','스커트'],'신발':['스니커즈','로퍼','부츠'],'가방':['숄더백','토트백']}
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
  if mode=='モノトーン': mode='모노톤'
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
 if bag=='숄더백':d.line((485,331,623,331),fill=edge,width=2)
 shoe=board['items']['신발'];c=board['colors']['신발']
 for x in [464,572]:
  if shoe=='부츠':
   d.rectangle((x,520,x+52,620),fill=c,outline=edge,width=3)
   d.rounded_rectangle((x,590,x+85,650),radius=14,fill=c,outline=edge,width=3)
  else:
   d.rounded_rectangle((x,560,x+77,635),radius=25,fill=c,outline=edge,width=3)
   if shoe=='스니커즈':
    for y in [580,591,602]: d.line((x+17,y,x+55,y),fill=edge,width=2)
   else:d.line((x+10,590,x+65,590),fill=edge,width=3)
  d.line((x,635 if shoe!='부츠' else 650,x+77,635 if shoe!='부츠' else 650),fill=edge,width=5)
 for i,k in enumerate(ITEMS):
  x=200+i*85;d.ellipse((x,720,x+45,765),fill=board['colors'][k],outline=edge,width=2)
 return im

def png(board):
 b=io.BytesIO();render(board).save(b,format='PNG');return b.getvalue()

def save_copy(name,tag):
 st.session_state.collection.append({'id':str(uuid.uuid4()),'name':name.strip() or '이름 없는 코디','tag':tag,'favorite':False,'board':copy.deepcopy(st.session_state.board)})

for k,v in {'board':default(),'undo':[],'redo':[],'collection':[],'compare':[],'widget_version':0}.items():
 if k not in st.session_state:st.session_state[k]=v
st.markdown('''<style>
#MainMenu,footer{visibility:hidden}.block-container{max-width:1000px;padding-top:1.2rem}
[data-testid="stAppViewContainer"]{background:#FCF9F5;color:#3E3B43}
h1{font-size:1.9rem!important;color:#57505D}.stButton button,.stDownloadButton button{border-radius:14px;min-height:42px}
[data-testid="stForm"]{background:#FFFDFC;border-radius:18px;border:1px solid #E6DDE6}
[data-testid="stVerticalBlock"]{gap:.65rem}input{font-size:16px!important}
</style>''',unsafe_allow_html=True)
st.title('🎨 色と服 · 색 조합 코디 공방')
st.caption('자료 준비 없이 시작하는 작은 스타일 실험실 · 도형 기반 코디 보드')
page=st.segmented_control('메뉴',['🏡 메인','🎨 작업실','🪞 비교실','🗂️ 컬렉션'],default='🏡 메인',label_visibility='collapsed')
b=st.session_state.board
if page=='🏡 메인':
 st.subheader('오늘은 어떤 색을 입혀볼까요? 🌷')
 st.write('내장된 옷과 팔레트로 자유롭게 조합해보세요. 사진이나 옷 정보는 필요 없어요.')
 left,right=st.columns([1,1])
 left.image(render(b),caption='현재 작업 · 작업실에서 이어서 편집')
 with right:
  st.markdown('### 작은 시작 가이드')
  st.write('① 프리셋 선택 → ② 작업실에서 편집 → ③ 비교·저장 → ④ 파일로 보관')
  preset=st.selectbox('준비된 스타일',list(PRESETS))
  if st.button('이 팔레트로 시작',use_container_width=True):
   new=default();new['colors']=dict(zip(ITEMS,PRESETS[preset]));commit(new);st.rerun()
  st.info(f"저장한 코디 {len(st.session_state.collection)}개 · 비교 후보 {len(st.session_state.compare)}개")
  st.warning('기록은 현재 접속 세션에만 보관됩니다. 아래 백업 파일을 내려받아 보관하세요.')
elif page=='🎨 작업실':
 left,right=st.columns([1.05,1])
 with right:
  st.subheader('아이템과 색상')
  version=st.session_state.widget_version
  with st.form('editor_'+str(version)):
   new=copy.deepcopy(b)
   for k in ITEMS:
    a,c=st.columns([2,1])
    new['items'][k]=a.selectbox(k,ITEMS[k],index=ITEMS[k].index(b['items'][k]),key=f'item_{k}_{version}')
    new['colors'][k]=c.color_picker('색상 · '+k,b['colors'][k],key=f'color_{k}_{version}')
    new['locks'][k]=st.checkbox(k+' 색상 잠금',b['locks'][k],key=f'lock_{k}_{version}')
   new['background']=st.color_picker('보드 배경',b['background'])
   apply=st.form_submit_button('편집 적용',use_container_width=True)
  if apply:
   commit(new);st.session_state.widget_version+=1;st.rerun()
  st.caption('색상 선택창에서 HEX 입력 가능 · 편집 적용 후 미리보기에 반영돼요.')
  mode=st.selectbox('색 조합 규칙',MODES)
  if st.button('🔀 잠금 제외 색 다시 조합',use_container_width=True):
   commit(generate(b,mode));st.session_state.widget_version+=1;st.rerun()
  st.caption('폼에서 바꾼 값은 먼저 편집 적용을 눌러주세요. 잠금은 자동 재조합에만 적용됩니다.')
  c1,c2,c3=st.columns(3)
  if c1.button('↶ 취소',disabled=not st.session_state.undo):
   st.session_state.redo.append(copy.deepcopy(b));st.session_state.board=st.session_state.undo.pop();st.session_state.widget_version+=1;st.rerun()
  if c2.button('↷ 다시',disabled=not st.session_state.redo):
   st.session_state.undo.append(copy.deepcopy(b));st.session_state.board=st.session_state.redo.pop();st.session_state.widget_version+=1;st.rerun()
  if c3.button('초기화'):
   commit(default());st.session_state.widget_version+=1;st.rerun()
 with left:
  st.image(render(b),caption='실제 피팅이 아닌 플랫레이 스타일 보드',use_container_width=True)
  st.write(' · '.join(f"{k} {b['colors'][k]}" for k in ITEMS))
  hsv=[colorsys.rgb_to_hsv(*(v/255 for v in rgb(c))) for c in b['colors'].values()]
  span=max(x[2] for x in hsv)-min(x[2] for x in hsv)
  st.info('아이템 사이 밝기 차이가 큰 조합이에요.' if span>.4 else '아이템의 밝기가 비교적 비슷한 조합이에요.')
  st.caption('색상값 기반 참고 설명이며 미적 평가·퍼스널컬러 진단이 아닙니다.')
  with st.expander('🎯 코디 미션'):
   unique=len(set(c.upper() for c in b['colors'].values()))
   st.write(('✅' if unique<=3 else '⬜')+f' 세 가지 색 이내 사용하기 · 현재 {unique}색')
   st.write(('✅' if all(x[1]<.12 for x in hsv) else '⬜')+' 무채색만으로 조합하기')
  if st.button('비교실에 현재 코디 추가',use_container_width=True):
   if len(st.session_state.compare)>=3:st.warning('비교실은 3개까지예요. 비교실에서 비운 후 추가해주세요.')
   else:st.session_state.compare.append(copy.deepcopy(b));st.success('비교 후보에 추가했어요.')
  with st.form('save'):
   name=st.text_input('코디 이름',max_chars=80)
   tag=st.selectbox('상황',['일상','출근','나들이','행사','여행'])
   if st.form_submit_button('컬렉션에 복사 저장',use_container_width=True):
    save_copy(name,tag);st.success('컬렉션에 저장했어요.')
  st.download_button('보드 PNG 다운로드',png(b),'style_board.png','image/png',use_container_width=True)
elif page=='🪞 비교실':
 st.subheader('작은 차이를 나란히 보기')
 neutral=st.toggle('배경을 같은 색으로 통일',value=True)
 if not st.session_state.compare: st.info('작업실에서 비교 후보를 추가해주세요. 최대 3개까지 비교해요.')
 else:
  for i,col in enumerate(st.columns(len(st.session_state.compare))):
   candidate=st.session_state.compare[i]
   with col:
    display=copy.deepcopy(candidate)
    if neutral:display['background']='#F2F1EE'
    st.image(render(display),caption=f'후보 {i+1}')
    for k in ITEMS:st.caption(f"{k}: {candidate['items'][k]} {candidate['colors'][k]}")
    if st.button('작업실로 가져오기',key='take'+str(i)):
     commit(candidate);st.session_state.widget_version+=1;st.success('가져왔어요. 작업실에서 편집하세요.')
    if st.button('후보 삭제',key='remove'+str(i)):
     st.session_state.compare.pop(i);st.rerun()
  if st.button('비교실 비우기'):st.session_state.compare=[];st.rerun()
else:
 st.subheader('나의 컬렉션')
 tag=st.selectbox('상황 필터',['전체','일상','출근','나들이','행사','여행'])
 fav=st.toggle('즐겨찾기만')
 records=[x for x in st.session_state.collection if (tag=='전체' or x['tag']==tag) and (not fav or x['favorite'])]
 if not records:st.info('아직 조건에 맞는 코디가 없어요. 작업실에서 저장해보세요.')
 for x in records:
  with st.expander(('★ ' if x['favorite'] else '')+x['name']+' · '+x['tag']):
   st.image(render(x['board']),width=320)
   a,c,d=st.columns(3)
   if a.button('불러오기',key='load'+x['id']):
    commit(x['board']);st.session_state.widget_version+=1;st.success('작업실에 불러왔어요. 원본 컬렉션은 변경되지 않습니다.')
   if c.button('☆ 즐겨찾기',key='fav'+x['id']):x['favorite']=not x['favorite'];st.rerun()
   confirm=d.checkbox('삭제 확인',key='confirm'+x['id'])
   if d.button('삭제',key='del'+x['id'],disabled=not confirm):
    st.session_state.collection=[y for y in st.session_state.collection if y['id']!=x['id']];st.rerun()
   st.download_button('PNG 다운로드',png(x['board']),'style_board.png','image/png',key='png'+x['id'])

st.divider()
with st.expander('📦 백업·복원 / 사용 안내'):
 backup={'schema':1,'board':st.session_state.board,'collection':st.session_state.collection}
 st.download_button('전체 작업 JSON 백업',json.dumps(backup,ensure_ascii=False,indent=2).encode('utf-8'),'style_backup.json','application/json',use_container_width=True)
 uploaded=st.file_uploader('이 앱에서 받은 JSON 백업 가져오기',type=['json'])
 if st.button('백업 복원',disabled=uploaded is None):
  try:
   if uploaded.size>2000000:raise ValueError('2MB 이하 파일만 가능해요.')
   data=json.loads(uploaded.getvalue())
   if data.get('schema')!=1:raise ValueError('지원하지 않는 백업 버전이에요.')
   board=valid_board(data['board']);collection=data['collection']
   if not isinstance(collection,list) or len(collection)>500:raise ValueError('컬렉션은 500개 이하만 가능해요.')
   cleaned=[]
   for x in collection:
    if not isinstance(x['name'],str) or len(x['name'])>80 or x['tag'] not in ['일상','출근','나들이','행사','여행'] or type(x['favorite']) is not bool:raise ValueError('컬렉션 형식 오류')
    cleaned.append({'id':str(uuid.uuid4()),'name':x['name'],'tag':x['tag'],'favorite':x['favorite'],'board':valid_board(x['board'])})
   # 검증을 모두 통과한 경우에만 원자적으로 교체합니다.
   st.session_state.restore_candidate={'board':board,'collection':cleaned}
  except (ValueError,KeyError,TypeError,AttributeError):st.error('올바른 앱 백업 파일인지 확인해주세요. 기존 작업은 유지됩니다.')
 if st.session_state.get('restore_candidate'):
  st.warning('복원하면 현재 작업과 컬렉션을 교체합니다. 먼저 백업하세요.')
  a,c=st.columns(2)
  if a.button('교체 확정'):
   restored=st.session_state.pop('restore_candidate');st.session_state.board=restored['board'];st.session_state.collection=restored['collection'];st.session_state.undo=[];st.session_state.redo=[];st.session_state.compare=[];st.session_state.widget_version+=1;st.rerun()
  if c.button('복원 취소'):st.session_state.pop('restore_candidate');st.rerun()
 st.caption('입력 자료·API 키·가입 불필요. 개인 온라인 저장은 지원하지 않으며 세션 종료 시 사라질 수 있어요. PNG는 보드와 색상칩을 포함합니다. 화면 색상은 실제 원단·조명 아래 색과 다를 수 있습니다. 메인 프리셋은 잠금 여부와 무관하게 새 기본 코디를 적용합니다.')
