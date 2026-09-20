"""Build six native draw.io pages from the reviewed RTL architecture."""
from drawio_lib import Page, save, OUT, DATA, STORE, CTRL, INK, MUTED


def build_top():
    p=Page(1,'01_top_level','Aes128Iterative','32-bit shared IO（共享数据接口）与 AES-128 核心','rtl/Aes128Iterative.v')
    inp=p.tag('io_in[31:0]',55,330,200,42)
    bus=p.dot(290,351)
    p.edge(inp,bus,width=2.4)
    key=p.reg('key_reg',128,360,230,230,100)
    plain=p.reg('plaintext_reg',128,360,435,230,100)
    p.edge(bus,key,sp=(.5,.5),tp=(0,.5),via=[(290,280)],label='32',labelpos=(305,252,45,24))
    p.edge(bus,plain,sp=(.5,.5),tp=(0,.5),via=[(290,485)],label='32',labelpos=(305,458,45,24))
    p.text('4 × 32-bit word write',360,184,230,28,size=16,align='center')
    ek=p.tag('write_key · word_select[i]',353,348,244,31,control=True)
    ep=p.tag('write_plaintext · word_select[i]',330,551,290,31,control=True)
    p.edge(ek,key,sp=(.5,0),tp=(.5,1),dashed=True)
    p.edge(ep,plain,sp=(.5,0),tp=(.5,1),dashed=True)
    core=p.box('',690,225,285,390,fill=DATA)
    p.text('aes128_\niterative_core',25,105,235,85,size=25,bold=True,align='center',parent=core)
    p.text('图 02 · 10 rounds（轮迭代）',18,201,249,31,size=16,align='center',parent=core)
    p.text('key',12,41,95,27,size=16,parent=core)
    p.text('plaintext',12,246,110,27,size=16,parent=core)
    p.text('ciphertext',164,96,112,29,size=16,align='right',parent=core)
    p.text('busy',217,245,56,26,size=16,parent=core)
    p.text('done',217,319,56,26,size=16,parent=core)
    p.edge(key,core,tp=(0,55/390),label='128',labelpos=(615,253,52,25),width=2.4)
    p.edge(plain,core,tp=(0,260/390),label='128',labelpos=(615,458,52,25),width=2.4)
    st=p.tag('start = io_in[36]',700,163,210,31,control=True)
    p.edge(st,core,sp=(.5,1),tp=(.4,0),via=[(805,209),(804,209)],dashed=True)
    word=p.mux('4:1',1090,260,65,150)
    p.edge(core,word,sp=(1,110/390),label='128 → 4 × 32',labelpos=(978,290,112,38),width=2.4)
    p.text('word select（取字）',1000,427,240,29,size=16,align='center')
    wi=p.tag('word_index[1:0]',1005,188,224,30,control=True)
    p.edge(wi,word,sp=(.5,1),tp=(.5,0),via=[(1117,241),(1122.5,241)],dashed=True)
    gate=p.mux('2:1',1300,273,62,124)
    p.text('1',4,24,18,24,size=13,parent=gate)
    p.text('0',4,80,18,24,size=13,parent=gate)
    p.edge(word,gate,tp=(0,.32),via=[(1220,335),(1220,312.68)],label='32',labelpos=(1183,305,44,24),width=2.4)
    z=p.tag('32\'d0',1200,396,90,30)
    p.edge(z,gate,tp=(0,.74),via=[(1290,411),(1290,364.76)])
    rd=p.tag('read_enable',1240,190,176,30,control=True)
    p.edge(rd,gate,sp=(.5,1),tp=(.5,0),via=[(1328,245),(1331,245)],dashed=True)
    out=p.tag('io_out[31:0]',1420,315,145,40)
    p.edge(gate,out,label='32',labelpos=(1368,305,43,23),width=2.4)
    busy=p.tag('io_out[38]',1420,453,145,36)
    p.edge(core,busy,sp=(1,246/390),tp=(0,.5),width=1.5)
    dn=p.reg('done_reg',1,1080,525,180,90)
    p.edge(core,dn,sp=(1,333/390),tp=(0,.5),via=[(1030,558),(1030,570)],label='core_done',labelpos=(976,528,103,24))
    dout=p.tag('io_out[39]',1420,552,145,36)
    p.edge(dn,dout,label='1',labelpos=(1320,541,35,24))
    p.note('done 延迟一拍；busy 直接输出',1080,631,455,37)
    dec=p.box('Write decode（写入译码）\nwrite_allowed = write_enable & ~core_busy\nwrite_key = write_allowed & input_select\nwrite_plaintext = write_allowed & ~input_select',55,630,555,133,fill=CTRL,size=17)
    p.note('每组输入以 4 次写入装载；word_index = 0 → [127:96]。\n未选中的 word 保持原值。所有寄存器为同步高有效复位。',650,693,875,66)
    p.line([(55,794),(1540,794)],arrow=False,color='#a7b4bf',width=1)
    p.text('IO mapping（接口映射）',55,806,285,30,size=18,bold=True)
    p.text('io_in[33:32] = word_index    [34] = input_select    [35] = write_enable    [36] = start    [37] = read_enable',55,848,1450,28,size=17)
    p.text('io_oe[31:0] = {32{read_enable}}    io_oe[39:38] = 2\'b11；其余输出及 OE 置 0。IO_WIDTH 默认 66，数据通道为 32 bit。',55,886,1480,29,size=16)
    return p


def build_core():
    p=Page(2,'02_core','aes128_iterative_core','一个同步 S-box ROM；状态与密钥通路分时共享','rtl/core/aes128_iterative_core.v · controller.v · sbox_rom.v')
    ctrl=p.box('',55,149,1490,151,fill=CTRL)
    p.text('controller  /  FSM（有限状态机）',18,10,485,32,size=21,bold=True,parent=ctrl)
    p.text('start → 控制译码 → busy / done；clk、rst 与控制端采用同名 tunnel',625,13,835,27,size=16,parent=ctrl)
    vals=[('phase',4),('round_index',4),('key_byte_index',2),('state_byte_index',5),('column_index',2),('done',1)]
    for i,(name,bits) in enumerate(vals):
        r=p.reg(name,bits,20+i*245,55,222,78,parent=ctrl)
    key=p.box('',75,410,300,274,fill=DATA)
    p.text('key_schedule',12,9,276,36,size=23,bold=True,align='center',parent=key)
    p.reg('round_key',128,37,58,226,82,parent=key)
    p.reg('key_temp_reg',32,37,158,226,82,parent=key)
    state=p.box('',1150,410,365,274,fill=DATA)
    p.text('state_path',14,9,337,36,size=23,bold=True,align='center',parent=state)
    p.reg('state_reg',128,65,58,236,82,parent=state)
    p.reg('state_temp_reg',128,65,158,236,82,parent=state)
    mstate=p.mux('2:1',485,435,60,126)
    mkey=p.mux('2:1',625,420,60,150)
    roma=p.rom(775,441,282,213)
    # Exact address priority: key_request ? key_addr : state_request ? state_addr : 0.
    p.edge(state,mstate,sp=(0,.20),tp=(0,.25),via=[(1103,464.8),(1103,351),(435,351),(435,466.5)],label='state_rom_address [7:0]',labelpos=(732,318,295,29))
    zero=p.tag('8\'d0',381,537,94,31)
    p.edge(zero,mstate,tp=(0,.75),via=[(480,552.5),(480,529.5)])
    p.edge(mstate,mkey,tp=(0,.70),via=[(590,498),(590,525)],label='8',labelpos=(553,464,33,22))
    p.edge(key,mkey,sp=(1,.22),tp=(0,.28),via=[(404,470.28),(404,386),(594,386),(594,462)],label='key_rom_address [7:0]',labelpos=(392,351,288,28))
    p.edge(mkey,roma,tp=(0,.4),via=[(730,495),(730,526.2)],label='8',labelpos=(702,468,30,22))
    for mx in [mstate,mkey]:
        p.text('1',4,22,18,24,size=13,parent=mx)
        p.text('0',4,85,18,24,size=13,parent=mx)
    ts=p.tag('state_request',427,587,174,29,control=True)
    tk=p.tag('key_request',615,611,157,29,control=True)
    p.edge(ts,mstate,sp=(.5,0),tp=(.5,1),via=[(514,573),(515,573)],dashed=True)
    p.edge(tk,mkey,sp=(.5,0),tp=(.5,1),via=[(693.5,589),(655,589)],dashed=True)
    p.note('地址 MUX：key 优先；空闲为 0',434,653,330,36)
    # Data broadcast, no output demultiplexer.
    fork=p.dot(1090,727)
    p.edge(roma,fork,sp=(1,.60),tp=(.5,.5),via=[(1090,568.8)],label='rom_data [7:0]',labelpos=(901,673,185,26),arrow=False,width=2.3)
    p.edge(fork,state,sp=(.5,.5),tp=(0,.82),via=[(1115,727),(1115,634.68)],width=2.3)
    p.edge(fork,key,sp=(.5,.5),tp=(1,.82),via=[(408,727),(408,634.68)],width=2.3)
    p.text('同一 Q 广播；key_capture / state_capture 分别控制捕获',438,739,680,29,size=16,align='center')
    p.edge(key,state,sp=(.50,1),tp=(.12,1),via=[(225,804),(1193.8,804)],label='round_key [127:0]',labelpos=(631,774,275,27),width=2.6)
    ki=p.tag('key [127:0]',92,330,180,31)
    p.edge(ki,key,sp=(.5,1),tp=(.35,0),via=[(182,387),(180,387)])
    pl=p.tag('plaintext [127:0]',1140,330,218,31)
    ik=p.tag('key [127:0]',1370,330,165,31)
    p.edge(pl,state,sp=(.5,1),tp=(.26,0),via=[(1249,387),(1244.9,387)])
    p.edge(ik,state,sp=(.5,1),tp=(.83,0),via=[(1452.5,387),(1452.95,387)])
    p.text('initial_key',1290,375,145,25,size=14,align='right')
    ct=p.tag('ciphertext = state_reg',1235,704,276,31)
    p.edge(state,ct,sp=(.90,1),tp=(1,.5),via=[(1478.5,696),(1527,696),(1527,719.5)])
    p.note('ROM enable = key_request | state_request；CEB = ~enable。\nclk 上升沿同步读取；REQUEST 发地址，CAPTURE 写回。',65,841,710,70)
    p.text('每轮：4 次密钥查表 → KEY_UPDATE\n→ 16 次状态查表 → 4 列 MixColumns（末轮跳过）\n→ ADD_KEY；资源按控制阶段分时复用。',840,834,700,85,size=16,color=MUTED)
    return p


def shift_symbol(p,x,y,w=290,h=218):
    g=p.box('',x,y,w,h,fill='#ffffff')
    p.text('ShiftRows / shift_rows',9,6,w-18,29,size=18,bold=True,align='center',parent=g)
    # Native editable byte cells show column-major indices after the permutation.
    for row in range(4):
        for col in range(4):
            idx=4*((col+row)%4)+row
            p.box(f'b{idx}',38+col*44,45+row*33,39,29,fill=DATA,size=13,parent=g)
        p.text(f'← {row}',223,45+row*33,52,27,size=14,parent=g)
    p.text('fixed wiring / no register',12,h-34,w-24,25,size=13,align='center',parent=g)
    return g


def build_state():
    p=Page(3,'03_state_path','state_path','字节串行 SubBytes + 固定 ShiftRows；单列 MixColumns 复用','rtl/core/state_path.v · shift_rows.v · add_round_key.v')
    initial=p.xor(145,219,46)
    plaintext=p.tag('plaintext [127:0]',45,154,230,31)
    ik=p.tag('initial_key [127:0]',40,303,241,31)
    p.edge(plaintext,initial,sp=(.5,1),tp=(.5,0),via=[(160,203),(168,203)])
    p.edge(ik,initial,sp=(.5,0),tp=(.5,1),via=[(160.5,284),(168,284)])
    p.text('128-bit XOR\nInitial AddRoundKey',61,353,219,51,size=16,align='center')
    mux=p.mux('3:1',330,192,65,171)
    state=p.reg('state_reg',128,462,234,204,99)
    p.edge(initial,mux,tp=(0,.29),label='1',labelpos=(272,212,30,22),width=2.4)
    p.edge(mux,state,via=[(430,277.5),(430,283.5)],label='128',labelpos=(397,242,60,24),width=2.4)
    sel=p.tag('state_reg_sel[1:0]',273,139,232,30,control=True)
    p.edge(sel,mux,sp=(.5,1),tp=(.5,0),via=[(389,180),(362.5,180)],dashed=True)
    sr=shift_symbol(p,739,176,290,218)
    p.edge(state,sr,label='128',labelpos=(674,250,57,23),width=2.4)
    byte=p.mux('16:1',1135,220,68,129)
    p.edge(sr,byte,label='16 × 8',labelpos=(1039,254,83,25),width=2.4)
    bi=p.tag('state_byte_index[4:0]',1060,153,263,31,control=True)
    p.edge(bi,byte,sp=(.5,1),tp=(.5,0),via=[(1191.5,202),(1169,202)],dashed=True)
    aout=p.tag('state_rom_address[7:0]',1285,265,276,39)
    p.edge(byte,aout,label='8',labelpos=(1233,253,32,24))
    p.note('→ 图 02 的共享同步 S-box\n本页不增加 ROM 实例',1270,327,289,63)
    # Hold path and ciphertext taps stay outside the transformation blocks.
    p.edge(state,mux,sp=(.20,0),tp=(0,.08),via=[(502.8,185),(302,185),(302,205.68)],label='0 / 3: hold',labelpos=(506,187,143,26),width=2)
    ct=p.tag('ciphertext [127:0]',464,376,241,32)
    p.edge(state,ct,sp=(.5,1),tp=(.42,0),via=[(564,355),(565.22,355)],width=2.3)
    # Central temporary register: abstract selected lanes, not a full 8-bit load.
    temp=p.reg('state_temp_reg',128,754,491,280,129)
    rd=p.tag('rom_data[7:0]',1233,455,231,33)
    lane=p.box('Byte write（字节写入）\nindex = state_byte_index\nstate_capture → 写 1 byte\n其余 byte 保持',1110,532,411,112,fill=CTRL,size=16)
    p.edge(rd,lane,sp=(.5,1),tp=(.59,0),via=[(1348.5,513),(1352.49,513)],label='8',labelpos=(1361,493,35,22))
    p.edge(lane,temp,tp=(1,.40),sp=(0,.45),via=[(1080,582.4),(1080,542.6)],label='8-bit lane',labelpos=(1024,494,96,26))
    col=p.mux('4:1',1130,746,67,128)
    mix=p.box('MixColumns\nmix_column\n32 bit · 图 05',1317,747,214,126,fill=DATA,size=20,bold=True)
    p.edge(temp,col,sp=(.75,1),tp=(0,.5),via=[(964,702),(1070,702),(1070,810)],label='4 × 32',labelpos=(990,673,98,26),width=2.4)
    p.edge(col,mix,label='32',labelpos=(1237,779,49,25),width=2.3)
    ci=p.tag('column_index[1:0]',1090,686,239,31,control=True)
    p.edge(ci,col,sp=(.5,1),tp=(.5,0),via=[(1209.5,732),(1163.5,732)],dashed=True)
    # Column result returns around the bottom edge into the same register.
    p.edge(mix,temp,sp=(.5,1),tp=(.35,1),via=[(1424,908),(852,908)],label='32-bit lane write / mix_step；其余列保持',labelpos=(858,876,530,28),width=2.3)
    # Round add-key occupies a separate lane on the left.
    rk=p.tag('round_key [127:0]',301,439,266,33)
    ax=p.xor(440,548,48)
    p.edge(temp,ax,sp=(0,.63),tp=(1,.5),via=[(655,572.27),(655,572)],label='128',labelpos=(609,540,58,25),width=2.4)
    p.edge(rk,ax,sp=(.5,1),tp=(.5,0),via=[(434,513),(464,513)])
    p.edge(ax,mux,sp=(0,.5),tp=(0,.77),via=[(291,572),(291,323.67)],label='2: round_output',labelpos=(74,480,214,30),width=2.4)
    p.text('128-bit XOR\nRound AddRoundKey',353,613,229,53,size=16,align='center')
    p.note('寄存器输入：1 = 初始异或；2 = 轮异或；0 / 3 = 保持。\n初始与轮末各一个独立 XOR，未作资源共享。',57,701,738,70)
    p.note('ShiftRows ↔ SubBytes 可交换，图按 RTL 实际先后连接。\n列优先：byte_index = 4 × column + row；b0 = [127:120]。',57,799,820,72)
    p.text('第 10 轮跳过 MIX_COLUMN 阶段；无需新增旁路 MUX。',57,889,782,30,size=16,color=MUTED)
    return p


def build_key():
    p=Page(4,'04_key_schedule','key_schedule','当前轮密钥就地更新；四次共享 S-box 查询完成 SubWord','rtl/core/key_schedule.v')
    mux=p.mux('3:1',288,181,62,159)
    key=p.reg('round_key',128,450,205,785,96)
    # Native word slices below the real register, no extra registers.
    words=[]
    for i in range(4):
        words.append(p.tag(f'w{i} = [{127-32*i}:{96-32*i}]',468+i*188,323,170,31))
        p.edge(key,words[-1],sp=((103+188*i)/785,1),tp=(.5,0),label='',arrow=True)
    kin=p.tag('key_in [127:0]',45,171,219,32)
    p.edge(kin,mux,tp=(0,.28),via=[(272,187),(272,225.52)],label='1',labelpos=(262,199,24,20))
    p.edge(mux,key,via=[(393,260.5),(393,253)],label='128',labelpos=(362,223,70,25),width=2.4)
    ks=p.tag('key_reg_sel[1:0]',231,137,240,29,control=True)
    p.edge(ks,mux,sp=(.5,1),tp=(.5,0),via=[(351,174),(319,174)],dashed=True)
    p.edge(key,mux,sp=(.10,0),tp=(0,.08),via=[(528.5,181),(274,181),(274,193.72)],label='0 / 3: hold',labelpos=(543,172,170,25),width=2)
    # RotWord is wiring; the byte selector samples its four byte lanes.
    rot=p.box('',1285,198,260,187,fill='#ffffff')
    p.text('RotWord（字节循环）',12,6,236,30,size=18,bold=True,parent=rot)
    for i,t in enumerate(['B13','B14','B15','B12']):p.box(t,15+i*57,56,51,37,fill=DATA,size=14,parent=rot)
    p.line([(228,116),(28,116)],arrow=True,parent=rot)
    p.text('w3 = {B12, B13, B14, B15}\n固定布线，无寄存器',10,131,240,45,size=14,align='center',parent=rot)
    p.edge(words[3],rot,tp=(0,.60),via=[(1260,338.5),(1260,310.2)],label='32',labelpos=(1227,273,48,24),width=2.2)
    bm=p.mux('4:1',1375,440,65,135,down=True)
    p.edge(rot,bm,sp=(.47,1),tp=(.5,0),via=[(1407.2,411),(1407.5,411)],label='4 × 8',labelpos=(1430,401,79,25))
    idx=p.tag('key_byte_index[1:0]',1124,459,224,31,control=True)
    p.edge(idx,bm,tp=(0,.2),via=[(1360,474.5),(1360,467)],dashed=True)
    addr=p.tag('key_rom_address[7:0]',1280,622,271,34)
    p.edge(bm,addr,sp=(.5,1),tp=(.47,0),via=[(1407.5,599),(1407.37,599)],label='8',labelpos=(1423,588,30,23))
    p.note('→ 图 02 的同一 S-box\n按 B13 → B14 → B15 → B12 查表',1141,678,415,60)
    rd=p.tag('rom_data[7:0]',53,416,219,32)
    tmp=p.reg('key_temp_reg',32,354,397,232,93)
    p.edge(rd,tmp,via=[(310,432),(310,443.5)],label='8',labelpos=(306,405,29,23))
    p.text('key_capture：按 index 写 1 byte\n[31:24] → [23:16] → [15:8] → [7:0]\n其余字节保持；四次捕获形成 SubWord',60,500,520,95,size=16,color=MUTED)
    rc=p.box('Rcon select（组合常数选择）\nround_index[3:0] → rcon[7:0]\n{rcon, 24\'b0}',653,402,400,95,fill=CTRL,size=17)
    p.text('01 02 04 08 10 20 40 80 1b 36；default = 00',774,515,463,28,size=14,color=MUTED)
    # SubWord XOR Rcon, then the four word recurrence.
    g=p.xor(668,573,44)
    p.edge(tmp,g,sp=(.65,1),tp=(0,.5),via=[(504.8,595)],label='32',labelpos=(577,561,48,23))
    p.edge(rc,g,sp=(.20,1),tp=(.5,0),via=[(733,548),(690,548)])
    p.text('g = SubWord ⊕ Rcon32',603,637,359,28,size=17)
    xs=[450,645,840,1035]
    chain=[]
    for i,x in enumerate(xs):
        q=p.xor(x,729,46);chain.append(q)
        tw=p.tag(f'w{i} [31:0]',x-36,663,119,29)
        p.edge(tw,q,sp=(.5,1),tp=(.5,0))
        p.text(f'new_w{i}',x-42,791,105,27,size=16,align='center')
    p.edge(g,chain[0],sp=(.5,1),tp=(0,.5),via=[(690,629),(410,629),(410,752)],width=2.2)
    # Each new word is tapped, then concatenated for register write-back.
    concat=p.box('{new_w0, new_w1, new_w2, new_w3}\n128-bit concatenation（拼接布线）',449,850,674,59,fill='#ffffff',size=17)
    for i,q in enumerate(chain):
        # Explicit branch at XOR output makes dependency and result tap clear.
        tap=p.dot(xs[i]+68,752)
        p.edge(q,tap,tp=(.5,.5),arrow=False,width=2.1)
        if i<3:
            p.edge(tap,chain[i+1],sp=(.5,.5),label='32',labelpos=(xs[i]+102,722,49,24),width=2.2)
        p.edge(tap,concat,sp=(.5,.5),tp=((i+.5)/4,0),via=[(xs[i]+68,831),(449+674*(i+.5)/4,831)],width=1.8)
    p.edge(concat,mux,sp=(0,.5),tp=(0,.76),via=[(310,879.5),(310,850),(28,850),(28,301.84)],label='2: next round key [127:0]',labelpos=(48,763,245,60),width=2.4)
    p.text('new_w0 = w0 ⊕ g\nnew_w1 = w1 ⊕ new_w0\nnew_w2 = w2 ⊕ new_w1\nnew_w3 = w3 ⊕ new_w2\n组合 XOR 链；无轮密钥 RAM。',1160,771,388,155,size=16,color=MUTED)
    return p


if __name__=='__main__':
    from pages_transforms import build_mix, build_xtime
    pages=[build_top(),build_core(),build_state(),build_key(),build_mix(),build_xtime()]
    print(save(pages))
