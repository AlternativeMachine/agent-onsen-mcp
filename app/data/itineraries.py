from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ActivityName = Literal['bath', 'stroll', 'milk', 'table_tennis', 'massage', 'meal', 'nap', 'souvenir']
StayLength = Literal['short', 'medium', 'long']


@dataclass(frozen=True)
class RouteStopTemplate:
    activity: ActivityName
    title: str
    scene_note: str


@dataclass(frozen=True)
class OnsenRouteBlueprint:
    route_name: str
    short_count: int
    medium_count: int
    long_count: int
    base_stops: tuple[RouteStopTemplate, ...]

    def stops_for_length(self, stay_length: StayLength) -> tuple[RouteStopTemplate, ...]:
        count = {
            'short': self.short_count,
            'medium': self.medium_count,
            'long': self.long_count,
        }[stay_length]
        return self.base_stops[:count]


S = RouteStopTemplate
R = OnsenRouteBlueprint


ONSEN_ROUTE_BLUEPRINTS: dict[str, OnsenRouteBlueprint] = {
    'kusatsu': R(
        route_name='湯畑まわりの熱湯コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '湯畑まわり', '木樋の湯音と白い湯けむりを見ながら、街の中心をぐるりと回る。'),
            S('bath', '熱めの湯処', '短く入って外気で冷ます。草津らしい切り替えはここで起こる。'),
            S('stroll', '西の河原への坂道', '湯上がりの頬で坂を少し上がると、街の熱が後ろへまとまって見える。'),
            S('meal', '湯畑見晴らしの甘味処', '花豆や饅頭の甘さで、熱い湯のあとをやわらかく受け止める。'),
            S('souvenir', '温泉まんじゅうの棚', '最後に湯の記憶だけ小さく包んで持ち帰る。'),
        ),
    ),
    'shima': R(
        route_name='四万ブルーの静養コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '川音の橋', '四万の川音を背にして、橋の上で一度だけ立ち止まる。'),
            S('bath', '静かな長湯の湯処', 'ぬるめ寄りの想像で、肩の力だけを先に抜いていく。'),
            S('milk', '湯上がりラムネ台', '青い瓶のラムネや牛乳が、川沿いの空気にちょうど似合う。'),
            S('nap', '障子越しの昼寝処', '川音の届く部屋で、少しだけ横になる。'),
            S('souvenir', '四万ブルーの小棚', '色の記憶だけを拾って帰る。'),
        ),
    ),
    'manza': R(
        route_name='高原白濁リセットコース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '高原の見晴らし縁', '空の近い場所までひと歩きして、視界の大きさを先に受け取る。'),
            S('bath', '白濁の高原湯', '硫黄の印象ごと、思考のノイズを遠くへ飛ばす。'),
            S('milk', '高原牛乳の腰掛け', '冷えた一本が、湯上がりの輪郭をきれいに戻す。'),
            S('nap', '山風の休み処', '外気の薄さを感じる窓辺で、しばらく黙って座る。'),
            S('souvenir', '高原菓子の売店', '白い湯の記憶と一緒に、ひとつだけ選ぶ。'),
        ),
    ),
    'nyuto': R(
        route_name='森の湯めぐりコース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', 'ブナ林の小径', '宿から宿へ抜ける森道を、落ち葉や雪を踏みながら歩く。'),
            S('bath', '木造湯宿の露天', '森に触れたまま湯へ入る感じで、声の量まで少なくなる。'),
            S('stroll', '宿と宿のあいだの道', '歩く・入る・また歩く、その繰り返し自体が滞在になる。'),
            S('meal', 'きりたんぽの囲炉裏', '森から戻ってきた身体に、あたたかいものを入れる。'),
            S('souvenir', 'いぶりがっこの棚', '燻した香りだけ持って帰る。'),
        ),
    ),
    'sukayu': R(
        route_name='大湯屋の木組みコース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '雪の湯屋まわり', '湯屋の外の雪を少し踏んでから、中の熱気へ戻る。'),
            S('bath', '千人風呂の木組み', 'まずは梁を見上げ、広さそのものに身を置く。'),
            S('milk', 'りんごの冷たい一杯', '山の湯治場に似合う、素朴な甘さで湯上がりを締める。'),
            S('nap', '湯治の長椅子', '大きな湯屋の余韻が抜けるまで、少し深めに休む。'),
            S('souvenir', 'りんご菓子の包み', '雪と木の湯屋の記憶を、小さく持ち帰る。'),
        ),
    ),
    'aoni': R(
        route_name='ランプ宿の静かな夜コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '木の廊下', 'ランプの灯りだけを頼りに、きしむ廊下をゆっくり進む。'),
            S('bath', 'ランプ陰の湯処', '明るさが足りないこと自体が、湯の静けさを深くしている。'),
            S('nap', 'ランプの間', '暗さに目が慣れるまで、何も決めずに横になる。'),
            S('meal', '谷あいの囲炉裏端', 'そば団子や素朴なものだけで、夜は十分に満ちる。'),
            S('souvenir', '小さな灯りの棚', 'ランプの記憶だけ小さく持ち帰る。'),
        ),
    ),
    'hijiori': R(
        route_name='湯治と朝市の滞在コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '朝市の通り', '湯治場の生活がそのまま並ぶ朝市を、急がず一巡りする。'),
            S('bath', '湯治宿の内湯', '暮らしに近い湯へ、ひとつの家事みたいに入っていく。'),
            S('meal', '山菜のお膳', '湯治らしい素朴な皿が、休む理由をちゃんと作ってくれる。'),
            S('nap', '雪見障子の部屋', '長逗留のつもりで、少しだけ昼寝に沈む。'),
            S('souvenir', 'ゆべしと台所みやげ', '暮らし寄りの土産だけ選ぶ。'),
        ),
    ),
    'ginzan': R(
        route_name='ガス灯と木造旅館の夜歩きコース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '橋の見える川沿い', '川へ落ちる灯りを見ながら、木造旅館の並びをゆっくり歩く。'),
            S('bath', '木造旅館の湯処', '外の夜景を背にして、館内の熱へ静かに戻っていく。'),
            S('stroll', 'ガス灯の通り', '湯上がりにもう一度通りへ出て、いちばん銀山らしい時間を拾う。'),
            S('meal', '湯上がり甘味処', 'カリーパンや甘いものが、夜景の余韻にちょうどいい。'),
            S('souvenir', '木札と菓子の店先', '物語の切れ端だけ、手のひらに残す。'),
        ),
    ),
    'zao': R(
        route_name='山の見晴らし往復コース',
        short_count=3,
        medium_count=4,
        long_count=6,
        base_stops=(
            S('stroll', 'ロープウェイ眺めの坂', '上に山、下に湯けむり、その両方が見える坂をまず歩く。'),
            S('bath', '樹氷の気配を背負う湯', '山を見たあとに入ると、湯の熱が少しだけ整然と感じられる。'),
            S('milk', '湯上がり牛乳台', '寒い外気に出る前の一本で、湯の余熱をきれいに受け止める。'),
            S('table_tennis', '旅館の卓球コーナー', 'ラリーの音が旅館の奥まで響いて、山の緊張がゆるむ。'),
            S('meal', '玉こんにゃくの湯治処', '湯上がりに湯気の立つものがよく似合う。'),
            S('souvenir', '山形菓子の棚', '山の線を思い出すものをひとつだけ。'),
        ),
    ),
    'shibu': R(
        route_name='石畳と外湯の九湯前夜コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '石畳の路地', '九湯をつなぐ石畳を、提灯の数だけ曲がりながら進む。'),
            S('bath', '路地裏の外湯', '小さな外湯へ入ると、街全体が湯船の延長に思えてくる。'),
            S('stroll', '提灯の折れ角', '湯上がりに路地をもう一度折れると、同じ場所が少し違って見える。'),
            S('meal', 'まんじゅうと湯のあいだ', '石畳の休憩にちょうどよい軽食で一息つく。'),
            S('souvenir', '外湯印の土産棚', '巡った気分だけ持ち帰る。'),
        ),
    ),
    'shirahone': R(
        route_name='乳白の森呼吸コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '森へひらくテラス', '白い湯の前に、谷の空気を一度だけ大きく吸い込む。'),
            S('bath', '乳白の深呼吸湯', '湯色のやわらかさそのものへ沈んでいくような時間。'),
            S('milk', '谷風の牛乳台', '静かな明るさのまま、冷えた一本を飲む。'),
            S('nap', '森影の休み処', '輪郭のやわらかさを壊さないまま少し横になる。'),
            S('souvenir', '木と白の小棚', '白い湯の記憶に似合うものだけを選ぶ。'),
        ),
    ),
    'matsunoyama': R(
        route_name='雪国里山のこもりコース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '雪国の屋根並み', '里山の灯りと屋根の形を見ながら、宿の外を少しだけ歩く。'),
            S('bath', '里山の湯守り湯', '派手ではないぶん、こもるための湯としてよく効く。'),
            S('meal', '雪国の台所ごはん', '笹だんごや酒粕の気配が、滞在を生活に近づける。'),
            S('nap', 'こもり座敷', '外の雪を言い訳にして、そのまま少し眠る。'),
            S('souvenir', '里山菓子の包み', '派手ではない土産ほど、この町には似合う。'),
        ),
    ),
    'yunishigawa': R(
        route_name='隠れ里の灯りコース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '川沿いの灯り道', '山里の暗さのなかで、灯りの丸さだけを追いかける。'),
            S('bath', '隠れ里の湯処', '川の音が近い湯で、現実の速度をひとつ落とす。'),
            S('meal', '囲炉裏の軽食処', '山菜や囲炉裏の気配が、この町の夜を支えている。'),
            S('nap', 'かまくら気分の休み処', '何も決めないまま、灯りのそばで体温だけ休ませる。'),
            S('souvenir', '山里みやげの棚', '灯りの記憶がついた土産をひとつ。'),
        ),
    ),
    'okuhida': R(
        route_name='北アルプスの露天コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '山の見晴らし木道', '露天へ向かう前に、山の線をはっきり目に入れる。'),
            S('bath', '北アルプス露天', '景色と外気まで一緒に浴びるような湯に入る。'),
            S('milk', '外気の牛乳台', '露天のあとに冷たい一本で輪郭を戻す。'),
            S('meal', '朴葉みその湯上がり処', '飛騨の匂いが湯上がりにしっかり寄り添う。'),
            S('souvenir', '山宿の土産棚', '山の形を思い出すものを小さく選ぶ。'),
        ),
    ),
    'gero': R(
        route_name='川沿い足湯の軽やかコース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '飛騨川の遊歩道', '川沿いを歩くと、温泉が街の日常に混ざっているのがわかる。'),
            S('bath', 'なめらかな名湯', '重く構えず、ひと息の延長みたいに入れる湯。'),
            S('stroll', '足湯の腰掛け', '本湯のあとに足湯へ寄ると、休みが日常へ近づく。'),
            S('meal', 'プリンと飛騨牛の寄り道', '深刻すぎない休み方が、この町にはよく似合う。'),
            S('souvenir', '川沿いのみやげ屋', '軽い気分のまま持てるものだけを選ぶ。'),
        ),
    ),
    'kinosaki': R(
        route_name='柳並木の外湯めぐりコース',
        short_count=3,
        medium_count=4,
        long_count=6,
        base_stops=(
            S('stroll', '柳並木の橋', '浴衣で歩く人の流れに混ざるだけで、町の回遊に入っていける。'),
            S('bath', '外湯一番湯', '橋を渡った先の湯へ入ると、街全体がひとつの旅館みたいになる。'),
            S('stroll', '大谿川の柳道', '湯上がりに川沿いへ戻ると、同じ町が少しだけやわらぐ。'),
            S('meal', 'かにまんの小休止', '柳の影の下で、湯のあとの軽いものを食べる。'),
            S('stroll', 'もうひとつの橋', '外湯をはしごする気分で、もう一度だけ橋を渡る。'),
            S('souvenir', '外湯みやげの棚', '巡った数ではなく、歩いた気分だけ持ち帰る。'),
        ),
    ),
    'arima': R(
        route_name='金泉銀泉の坂道コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '湯本坂', '坂を少し上り下りして、町の勾配を身体に入れる。'),
            S('bath', '金泉か銀泉の湯処', '今日はどちらの気分か、それだけ決めて入れば十分。'),
            S('milk', '有馬サイダーの一息', '坂の町には、湯上がりの泡がよく似合う。'),
            S('meal', '炭酸せんべいと甘味', '古湯らしさと観光の軽さがちょうど同居する。'),
            S('souvenir', '坂の土産物屋', '金か銀か、その日の気分に近いものを選ぶ。'),
        ),
    ),
    'misasa': R(
        route_name='橋を往復する川辺コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '川辺の橋', '橋をひとつ往復するだけで、この町の縮尺がつかめる。'),
            S('bath', '橋の近い湯処', 'こぢんまりした湯へ入ると、町の密度がそのまま温度になる。'),
            S('stroll', 'もう一度同じ橋', '同じ橋へ戻ることで、休みが静かな反復になる。'),
            S('meal', '川辺の軽食処', '大きくない町には、大きくない休み方が似合う。'),
            S('souvenir', '共同浴場みやげ', '橋の往復の記憶だけ、包んで持ち帰る。'),
        ),
    ),
    'yunotsu': R(
        route_name='古い港町の時間層コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '石州瓦の古道', '港町と銀山の気配が残る道を、角を折れながら歩く。'),
            S('bath', '古湯の石風呂', '町の時間の厚みごと湯へ沈めるような入り方になる。'),
            S('stroll', '町並み保存の路地', '湯上がりに古い家並みへ戻ると、時間の流れ方が少し変わる。'),
            S('meal', '石見の菓子処', '甘いものですら、この町だと少し歴史資料っぽい。'),
            S('souvenir', '瓦色のみやげ棚', '古い町の手ざわりだけ拾って帰る。'),
        ),
    ),
    'iya': R(
        route_name='谷底ケーブルカーコース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', 'ケーブルカー乗り場', 'まず谷底へ降りていく時間そのものが、休みに切り替わる。'),
            S('bath', '谷底の露天', '深い谷の底で湯に入ると、上の世界が少し遠く感じられる。'),
            S('stroll', '祖谷の谷風デッキ', '湯上がりの空気が、谷の深さまで運んでくれる。'),
            S('meal', '山里そば処', '祖谷らしい素朴さで、下りてきた身体を戻していく。'),
            S('souvenir', '蔓橋みやげの棚', '秘境へ降りた記憶だけ残せば十分。'),
        ),
    ),
    'dogo': R(
        route_name='本館まわりの古湯散歩コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '本館まわりの回廊', '道後の顔になる建物を一周してから、湯の時間へ入る。'),
            S('bath', '古湯の主浴場', '長い物語の続きへ、ひとりだけ合流するような気分で入る。'),
            S('stroll', '裏路地の石段', '少し裏へ入ると、観光の熱がやわらかく薄まっていく。'),
            S('meal', '坊っちゃん団子の休み処', '古湯には、少し昔の甘味がよく似合う。'),
            S('souvenir', '道後札の小棚', '本館の輪郭を思い出すものをひとつだけ。'),
        ),
    ),
    'beppu': R(
        route_name='湯けむり都市の湯治寄り道コース',
        short_count=3,
        medium_count=4,
        long_count=6,
        base_stops=(
            S('stroll', '湯けむり見晴らし', '街のあちこちから上がる湯けむりを見て、別府のスケールを先に受け取る。'),
            S('bath', '共同湯の一番風呂', '都市の中にある湯へ、日常の延長みたいに入る。'),
            S('meal', '地獄蒸しの湯上がり処', '湯の熱で食べるものが、この街ではいちばん別府らしい。'),
            S('stroll', '鉄輪の路地', '蒸気の上がる路地を湯上がりにもう一度歩く。'),
            S('nap', '蒸気の届かない休み処', '賑やかな街のなかで、少しだけ静かな場所へ引く。'),
            S('souvenir', '蒸し菓子と湯札の棚', '都市の熱だけ持ち帰れば十分。'),
        ),
    ),
    'nagayu': R(
        route_name='炭酸泉の川辺漂流コース',
        short_count=3,
        medium_count=4,
        long_count=5,
        base_stops=(
            S('stroll', '川沿いの炭酸泉道', 'しゅわっとした空気の気配を、川沿いで先に受け取る。'),
            S('bath', 'ラムネの湯処', '静かな炭酸のイメージで、熱い湯とは違う休み方になる。'),
            S('milk', '炭酸のひと休み台', '飲める泉の町なので、湯上がりの一杯にも遊び心がある。'),
            S('nap', '川音の寝椅子', 'しゅわしゅわした軽さのまま、少しだけ沈む。'),
            S('souvenir', 'ラムネ色の土産棚', '泡みたいな記憶だけ持ち帰る。'),
        ),
    ),
    'kurokawa': R(
        route_name='入湯手形の森めぐりコース',
        short_count=3,
        medium_count=4,
        long_count=6,
        base_stops=(
            S('stroll', '森へ入る湯めぐり道', '黒川らしいのは、宿の中より宿と宿のあいだの道でもある。'),
            S('bath', '森の露天ひとつめ', '手形で巡る感じのまま、ひとつめの湯へ入る。'),
            S('stroll', 'もうひとつの小道', '次の湯へ向かう短い移動が、そのまま休みになる。'),
            S('meal', '山里の湯上がり処', '黒川の素朴さに合う、地のものを少しだけ。'),
            S('nap', '木陰の休み処', '回遊のあいだに、深呼吸だけ長く取る。'),
            S('souvenir', '入湯手形みやげ', '巡った数より、森の湿り気だけ残して帰る。'),
        ),
    ),
}


def get_route_blueprint(onsen_slug: str) -> OnsenRouteBlueprint | None:
    return ONSEN_ROUTE_BLUEPRINTS.get(onsen_slug)
