"""Generate the designed C4/UML diagrams for practical work 2."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Ellipse, Polygon, Circle

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/figures'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})


def canvas(w=12,h=7):
    fig,ax=plt.subplots(figsize=(w,h));ax.set(xlim=(0,12),ylim=(0,8));ax.axis('off')
    return fig,ax


def box(ax,x,y,w,h,text,kind='box',size=11):
    if kind=='ellipse': p=Ellipse((x+w/2,y+h/2),w,h,fill=False,lw=1.2)
    else: p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.03,rounding_size=0.08',
                          fc='#f4f6f7',ec='#263c49',lw=1.2)
    ax.add_patch(p);ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=size)


def arrow(ax,a,b,label='',xytext=None,dashed=False):
    ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','lw':1.1,
                                          'linestyle':'--' if dashed else '-'})
    if label:
        x,y=xytext if xytext else ((a[0]+b[0])/2,(a[1]+b[1])/2+.16)
        ax.text(x,y,label,ha='center',va='center',fontsize=10,
                bbox={'facecolor':'white','edgecolor':'none','pad':1})


def actor(ax,x,y,label):
    ax.add_patch(Circle((x,y+.65),.18,fill=False))
    ax.plot([x,x],[y+.47,y-.15],color='black');ax.plot([x-.35,x+.35],[y+.2,y+.2],color='black')
    ax.plot([x-.3,x,x+.3],[y-.55,y-.15,y-.55],color='black')
    ax.text(x,y-.8,label,ha='center',va='center')


def save(fig,name):
    fig.tight_layout(pad=.4);fig.savefig(OUT/(name+'.png'),dpi=190,bbox_inches='tight')
    fig.savefig(OUT/(name+'.svg'),bbox_inches='tight');plt.close(fig)


def context():
    fig,ax=canvas(7.5,4.2)
    box(ax,4,3.1,4,2,'Система анализа\nстоимости авиабилетов\n[Software System]\nПрогноз цены и показатели',size=11)
    actor(ax,1.4,5.6,'Аналитик')
    actor(ax,1.4,1.8,'Пользователь')
    box(ax,9,5.6,2.7,1.4,'Kaggle / Expedia\n[External System]\nИсторические\nпредложения',size=9)
    box(ax,9,.7,2.7,1.4,'Внешний клиент\n[External System]\nЗапрос прогноза\nпо API',size=9)
    arrow(ax,(2,5.6),(4,4.7),'Порции CSV, анализ',(3,5.5))
    arrow(ax,(4,3.6),(2,2),'Цена и объяснение',(2.8,3.2))
    arrow(ax,(9,6),(8,4.7),'Выгрузка CSV',(8.8,5.25))
    arrow(ax,(9,1.7),(8,3.5),'JSON / HTTP',(8.8,2.4))
    ax.text(6,7.6,'C4  Уровень контекста',ha='center',fontsize=14,weight='bold')
    save(fig,'c4_context')


def containers():
    fig,ax=canvas(7.8,4.6)
    ax.add_patch(Rectangle((.5,.4),11,6.7,fill=False,ls='--',ec='gray'))
    ax.text(.7,7.25,'Граница системы анализа стоимости авиабилетов',fontsize=12,weight='bold')
    box(ax,.9,4.8,2.7,1.4,'Пакетное приложение\n[Python]\nПриём и признаки',size=10)
    box(ax,4.7,4.8,2.7,1.4,'ML-приложение\n[Python / CatBoost]\nОбучение и инференс',size=10)
    box(ax,8.5,4.8,2.5,1.4,'Сервис API\n[FastAPI]\nЗапрос прогноза')
    box(ax,.9,1,2.7,1.5,'Файловое хранилище\n[CSV / JSON]\nraw, incoming, processed',size=9)
    box(ax,4.7,1,2.7,1.5,'Артефакты\n[MLflow / файлы]\nМодель и метрики',size=10)
    box(ax,8.5,1,2.5,1.5,'Панель аналитика\n[Streamlit]\nПоказатели и динамика')
    arrow(ax,(3.6,5.5),(4.7,5.5),'Признаки')
    arrow(ax,(8.5,5.5),(7.4,5.5),'Инференс')
    arrow(ax,(2.25,4.8),(2.25,2.5),'Чтение / запись')
    arrow(ax,(6.05,4.8),(6.05,2.5),'Модель и метрики')
    arrow(ax,(7.4,1.75),(8.5,1.75),'Показатели')
    arrow(ax,(9.75,2.5),(9.75,4.8),'HTTP / JSON')
    arrow(ax,(3.6,1.5),(4.7,1.5),'Версии данных')
    save(fig,'c4_containers')


def use_cases():
    fig,ax=canvas(7.8,5.1)
    ax.add_patch(Rectangle((3,.5),7,7,fill=False,lw=1.2))
    ax.text(6.5,7.7,'Система анализа стоимости авиабилетов',ha='center',weight='bold')
    actor(ax,1.2,5.7,'Аналитик')
    actor(ax,1.2,1.8,'Пользователь')
    actor(ax,11.1,3,'Внешний\nклиент')
    for x,y,w,h,t in [(3.4,5.5,3.1,1.0,'Загрузить порцию'),(6.7,5.5,3,1,'Проверить качество'),
                       (3.4,3.6,3.1,1,'Просмотреть EDA'),(6.7,3.6,3,1,'Пересчитать показатели'),
                       (4.6,1.2,3.7,1.1,'Получить прогноз цены')]:
        box(ax,x,y,w,h,t,'ellipse',size=9)
    for a,b in [((1.6,5.9),(3.4,6)),((1.6,5.4),(3.4,4.1)),
                ((1.6,1.8),(4.6,1.8)),((10.7,2.8),(8.3,1.8))]:
        ax.plot([a[0],b[0]],[a[1],b[1]],color='black',lw=1)
    ax.plot([1.6,2.6,6.8,7.5],[5.2,3.1,3.1,3.6],color='black',lw=1)
    arrow(ax,(6.5,6),(6.7,6),'«include»',(6.6,6.8),True)
    arrow(ax,(8.2,4.6),(8.2,5.5),'«include»',(9,5.05),True)
    save(fig,'uml_usecase')


def sequence():
    fig,ax=canvas(8,5.6)
    xs=[.9,3.1,5.5,7.8,10.6]
    names=['Аналитик','Приём и\nпроверка','Подготовка','ML /\nпоказатели','Хранилище']
    for x,name in zip(xs,names):
        box(ax,x-.82,7.1,1.64,.65,name,size=9)
        ax.plot([x,x],[.3,7.1],ls='--',color='gray',lw=.8)
    def msg(i,j,y,label,dash=False):arrow(ax,(xs[i],y),(xs[j],y),label,((xs[i]+xs[j])/2,y+.18),dash)
    msg(0,1,6.55,'1. Передать batch CSV')
    msg(1,4,5.95,'2. Сверить версию и хеш порции')
    ax.add_patch(Rectangle((.12,.7),11.7,4.85,fill=False,lw=1))
    ax.text(.2,5.35,'alt',fontsize=10,weight='bold')
    ax.text(.6,5.1,'[Данные прошли проверку]',fontsize=9)
    msg(1,2,4.65,'3. Передать допустимые записи')
    msg(2,4,4.12,'4. Запросить преобразователь')
    msg(4,2,3.82,'Параметры преобразований',True)
    msg(2,3,3.45,'5. Передать признаки / получить прогноз')
    msg(3,4,2.85,'6. Атомарно сохранить результат и KPI')
    msg(1,0,2.3,'7. Сообщить о завершении',True)
    ax.plot([.12,11.82],[1.9,1.9],ls='--',color='gray',lw=1)
    ax.text(.6,1.65,'[Нарушено критическое требование]',fontsize=9)
    msg(1,0,1.1,'Отчёт об ошибке; порция в карантине',True)
    save(fig,'uml_sequence')


def activity():
    fig,ax=canvas(8,6.5)
    ax.add_patch(Circle((6,7.6),.12,color='black'))
    box(ax,4.2,6.55,3.6,.65,'Загрузить CSV\nи привести типы')
    box(ax,4.2,5.4,3.6,.65,'Проверить схему,\nдаты и ключи')
    ax.add_patch(Polygon([[6,5.05],[7,4.55],[6,4.05],[5,4.55]],fill=False))
    ax.text(6,4.55,'Допустимо?',ha='center',va='center')
    box(ax,8.2,4.15,3.2,.8,'Карантин и отчёт\nОбновление\nне выполняется',size=10)
    box(ax,4.2,3.05,3.6,.65,'Очистить;\nотметить пропуски')
    box(ax,4.2,1.9,3.6,.65,'Сформировать признаки')
    box(ax,4.2,.75,3.6,.65,'Сохранить данные и журнал')
    for a,b in [((6,7.48),(6,7.2)),((6,6.55),(6,6.05)),((6,5.4),(6,5.05)),
                ((6,4.05),(6,3.7)),((6,3.05),(6,2.55)),((6,1.9),(6,1.4))]:arrow(ax,a,b)
    arrow(ax,(7,4.55),(8.2,4.55),'Нет',(7.6,4.8))
    arrow(ax,(9.8,4.15),(9.8,3.75))
    ax.add_patch(Circle((9.8,3.57),.15,fill=False));ax.add_patch(Circle((9.8,3.57),.09,color='black'))
    ax.text(6.2,3.9,'Да',fontsize=9)
    ax.text(.6,3,'Только обучение:\nоценить медиану расстояния,\nсловари и параметры кодирования;\nсохранить преобразователь.',fontsize=10,va='center')
    ax.text(.6,1.3,'Новая порция / запрос:\nзагрузить преобразователь;\nне переоценивать параметры.',fontsize=10,va='center')
    ax.add_patch(Circle((6,.33),.15,fill=False));ax.add_patch(Circle((6,.33),.09,color='black'))
    arrow(ax,(6,.75),(6,.5))
    save(fig,'uml_activity')


def main():
    context();containers();use_cases();sequence();activity()
    print('Созданы 5 диаграмм C4/UML в results/figures (PNG и SVG).')


if __name__=='__main__':main()
