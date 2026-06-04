#!/usr/bin/env bash
cd /Users/yinshawnrao/explorer/cc-media/sandbox/fws-no-jay
F=renders/fws-no-jay.mp4; D=qa_frames
mkdir -p $D/full
gf(){ ffmpeg -nostdin -v error -i "$F" -ss $1 -frames:v 1 -vf "scale=216:384" $D/full/$2.png -y </dev/null; }
# cover/hook/intro
gf 0 a01_cover; gf 8 a02_hkA; gf 13 a03_hkB; gf 19 a04_hkC
# s1
gf 24 b01_s1card; gf 52 b02_s1cho; gf 69 b03_s1mid; gf 74.6 b04_tr1
# s2
gf 78 c01_s2card; gf 103 c02_s2cho; gf 122 c03_s2mid; gf 128.5 c04_tr2
# s3
gf 132 d01_s3card; gf 155 d02_s3cho; gf 173 d03_s3mid; gf 178 d04_tr3
# s4
gf 181 e01_s4card; gf 208 e02_s4cho; gf 226 e03_s4mid; gf 232.2 e04_tr4
# s5
gf 235 f01_s5card; gf 262 f02_s5cho; gf 280 f03_s5mid; gf 285.9 f04_tr5
# s6
gf 289 g01_s6card; gf 312 g02_s6cho; gf 330 g03_s6mid; gf 337.6 g04_tr6
# s7
gf 341 h01_s7card; gf 363 h02_s7cho; gf 382 h03_s7mid
# outro
gf 402 i01_outro; gf 410 i02_outro
# grids
cd $D/full
ffmpeg -v error -i a01_cover.png -i a02_hkA.png -i a03_hkB.png -i a04_hkC.png -i b01_s1card.png -i b02_s1cho.png -i b03_s1mid.png -i b04_tr1.png -filter_complex "hstack=8" ../G1_intro_s1.png -y
ffmpeg -v error -i c01_s2card.png -i c02_s2cho.png -i c03_s2mid.png -i c04_tr2.png -i d01_s3card.png -i d02_s3cho.png -i d03_s3mid.png -i d04_tr3.png -filter_complex "hstack=8" ../G2_s2s3.png -y
ffmpeg -v error -i e01_s4card.png -i e02_s4cho.png -i e03_s4mid.png -i e04_tr4.png -i f01_s5card.png -i f02_s5cho.png -i f03_s5mid.png -i f04_tr5.png -filter_complex "hstack=8" ../G3_s4s5.png -y
ffmpeg -v error -i g01_s6card.png -i g02_s6cho.png -i g03_s6mid.png -i g04_tr6.png -i h01_s7card.png -i h02_s7cho.png -i h03_s7mid.png -i i01_outro.png -i i02_outro.png -filter_complex "hstack=9" ../G4_s6s7outro.png -y
echo "QA grids built"
