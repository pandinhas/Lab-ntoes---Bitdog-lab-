# BitDogLab V7 - Quiz Musical + Compositor (menu inicial)
# OLED SH1107 128x128, joystick, 3 botoes, buzzer, LEDs e matriz 5x5.
# Salve na placa como /main.py (junto com sh1107.py) para iniciar sozinho.
# Para voltar ao menu: aperte o botao RESET da placa.
#
# Botoes (conforme BIH V7): A = GPIO5, B = GPIO6, C = GPIO10.
# Joystick: X=GPIO27, Y=GPIO26, SW=GPIO22 (mapeamento invertido validado).

from machine import Pin, ADC, I2C, PWM
from sh1107 import SH1107_I2C
import neopixel
import utime
import urandom

# =====================================================================
# HARDWARE COMUM
# =====================================================================

BTN_A = Pin(5, Pin.IN, Pin.PULL_UP)
BTN_B = Pin(6, Pin.IN, Pin.PULL_UP)
BTN_C = Pin(10, Pin.IN, Pin.PULL_UP)
JOY_SW = Pin(22, Pin.IN, Pin.PULL_UP)
JOY_X = ADC(Pin(27))
JOY_Y = ADC(Pin(26))

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=100000)
oled = SH1107_I2C(128, 128, i2c, addr=0x3C)

buzzer = PWM(Pin(21))
buzzer.freq(440)
buzzer.duty_u16(0)

verde = Pin(11, Pin.OUT)
vermelho = Pin(13, Pin.OUT)

pixels = neopixel.NeoPixel(Pin(7), 25)
LED_MATRIX = [
    [24, 23, 22, 21, 20],
    [15, 16, 17, 18, 19],
    [14, 13, 12, 11, 10],
    [5, 6, 7, 8, 9],
    [4, 3, 2, 1, 0],
]
LED_ORDER = [led for row in LED_MATRIX for led in row]
COLORS = [
    (45, 0, 0),    # Compasso 1 - vermelho
    (45, 28, 0),   # Compasso 2 - amarelo
    (0, 40, 0),    # Compasso 3 - verde
    (0, 25, 40),   # Compasso 4 - ciano
    (0, 0, 50),    # Compasso 5 - azul
]


def apagar_leds():
    verde.value(0)
    vermelho.value(0)


def clear_lights():
    pixels.fill((0, 0, 0))
    pixels.write()


def esperar_soltar(pino):
    while pino.value() == 0:
        utime.sleep_ms(15)


def eixo(adc, nome_baixo, nome_alto):
    """Le um eixo do joystick e espera voltar ao centro (histerese)."""
    valor = adc.read_u16()
    if valor < 17000:
        while adc.read_u16() < 24000:
            utime.sleep_ms(15)
        return nome_baixo
    if valor > 48000:
        while adc.read_u16() > 41000:
            utime.sleep_ms(15)
        return nome_alto
    return None


def ler_evento(botoes):
    """Espera um evento: joystick (CIMA/BAIXO/ESQUERDA/DIREITA) ou botao.
    botoes = ((pino, "NOME"), ...)"""
    while True:
        # Mapeamento invertido validado na placa (BIH: INVERT_X/INVERT_Y).
        ev = eixo(JOY_X, "DIREITA", "ESQUERDA")
        if ev:
            return ev
        ev = eixo(JOY_Y, "CIMA", "BAIXO")
        if ev:
            return ev
        for pino, nome in botoes:
            if pino.value() == 0:
                utime.sleep_ms(25)
                if pino.value() == 0:
                    esperar_soltar(pino)
                    return nome
        utime.sleep_ms(20)


def tela(linhas):
    oled.fill(0)
    for texto, x, y in linhas:
        oled.text(texto, x, y)
    oled.show()


def message(msg):
    oled.fill(0)
    oled.text(msg[:16], 0, 50)
    oled.show()
    utime.sleep_ms(750)


# =====================================================================
# MENU INICIAL
# =====================================================================

def menu():
    opcoes = ("QUIZ MUSICAL", "COMPOSITOR")
    sel = 0
    while True:
        oled.fill(0)
        oled.text("BITDOGLAB V7", 16, 6)
        oled.text("MENU INICIAL", 16, 20)
        for i in range(len(opcoes)):
            y = 46 + 16 * i
            if i == sel:
                oled.fill_rect(4, y - 3, 120, 14, 1)
                oled.text(opcoes[i], 12, y, 0)
            else:
                oled.text(opcoes[i], 12, y)
        oled.text("Y: ESCOLHE", 16, 88)
        oled.text("SW/A: ENTRA", 12, 100)
        oled.text("RESET: MENU", 16, 114)
        oled.show()

        ev = ler_evento(((BTN_A, "OK"), (JOY_SW, "OK")))
        if ev in ("CIMA", "ESQUERDA"):
            sel = (sel - 1) % len(opcoes)
        elif ev in ("BAIXO", "DIREITA"):
            sel = (sel + 1) % len(opcoes)
        else:
            return sel


# =====================================================================
# QUIZ MUSICAL - escala de Do maior completa
# =====================================================================

ESCALA = [
    ("DO", 262), ("RE", 294), ("MI", 330), ("FA", 349),
    ("SOL", 392), ("LA", 440), ("SI", 494),
]
TOTAL_RODADAS = 7


def tocar_nota(freq):
    buzzer.freq(freq)
    buzzer.duty_u16(32768)
    utime.sleep_ms(900)
    buzzer.duty_u16(0)


def apresentar_notas():
    """Rodada de apresentacao: toca DO..SI em ordem. A pula."""
    for i in range(len(ESCALA)):
        nome, freq = ESCALA[i]
        oled.fill(0)
        oled.text("OUCA AS NOTAS", 8, 0)
        oled.text("%d Hz" % freq, 36, 12)
        for k in range(len(ESCALA)):
            y = 26 + 10 * k
            if k == i:
                oled.fill_rect(30, y - 1, 68, 10, 1)
                oled.text(ESCALA[k][0], 36, y, 0)
            else:
                oled.text(ESCALA[k][0], 36, y)
        oled.text("A: PULAR", 28, 106)
        oled.show()

        buzzer.freq(freq)
        buzzer.duty_u16(32768)
        t0 = utime.ticks_ms()
        pular = False
        while utime.ticks_diff(utime.ticks_ms(), t0) < 900:
            if BTN_A.value() == 0:
                pular = True
                break
            if utime.ticks_diff(utime.ticks_ms(), t0) >= 700:
                buzzer.duty_u16(0)
            utime.sleep_ms(15)
        buzzer.duty_u16(0)
        if pular:
            esperar_soltar(BTN_A)
            return


def desenhar_pergunta(rodada, sel):
    oled.fill(0)
    oled.text("RODADA %d/%d" % (rodada + 1, TOTAL_RODADAS), 0, 0)
    oled.text("QUAL NOTA?", 0, 12)
    for i in range(len(ESCALA)):
        y = 26 + 10 * i
        if i == sel:
            oled.fill_rect(30, y - 1, 68, 10, 1)
            oled.text(ESCALA[i][0], 36, y, 0)
        else:
            oled.text(ESCALA[i][0], 36, y)
    oled.text("A:OK B/SW:OUVIR", 4, 100)
    oled.text("Y:ESCOLHE", 4, 112)
    oled.show()


def obter_resposta(freq, rodada):
    sel = 0
    while True:
        desenhar_pergunta(rodada, sel)
        ev = ler_evento(((BTN_A, "CONFIRMAR"), (BTN_B, "REPETIR"),
                         (JOY_SW, "REPETIR")))
        if ev in ("CIMA", "ESQUERDA"):
            sel = (sel - 1) % len(ESCALA)
        elif ev in ("BAIXO", "DIREITA"):
            sel = (sel + 1) % len(ESCALA)
        elif ev == "REPETIR":
            tocar_nota(freq)
        else:
            return sel


def esperar_A():
    while True:
        if BTN_A.value() == 0:
            utime.sleep_ms(30)
            if BTN_A.value() == 0:
                esperar_soltar(BTN_A)
                return
        utime.sleep_ms(20)


def quiz():
    while True:
        apagar_leds()
        tela([
            ("QUIZ MUSICAL", 12, 8),
            ("ESCALA DO MAIOR", 4, 26),
            ("OUCA A NOTA E", 12, 46),
            ("ESCOLHA NA LISTA", 0, 58),
            ("Y: ESCOLHE", 16, 76),
            ("A: CONFIRMA", 12, 88),
            ("B/SW: REPETIR", 12, 100),
            ("A: COMECAR", 16, 118),
        ])
        esperar_A()

        apresentar_notas()

        pontos = 0
        anterior = -1

        for rodada in range(TOTAL_RODADAS):
            apagar_leds()

            indice = urandom.getrandbits(8) % len(ESCALA)
            while indice == anterior:
                indice = urandom.getrandbits(8) % len(ESCALA)
            anterior = indice
            nome, freq = ESCALA[indice]

            desenhar_pergunta(rodada, 0)
            utime.sleep_ms(500)
            tocar_nota(freq)

            resposta = obter_resposta(freq, rodada)

            if resposta == indice:
                pontos += 1
                verde.value(1)
                linhas = [
                    ("ACERTOU!", 25, 10),
                    ("NOTA: " + nome, 15, 34),
                    (str(freq) + " Hz", 30, 50),
                    ("PONTOS: " + str(pontos), 15, 80),
                    ("PROXIMA...", 20, 108),
                ]
            else:
                vermelho.value(1)
                linhas = [
                    ("ERROU!", 33, 10),
                    ("NOTA: " + nome, 15, 34),
                    (str(freq) + " Hz", 30, 50),
                    ("VOCE: " + ESCALA[resposta][0], 15, 64),
                    ("PONTOS: " + str(pontos), 15, 84),
                    ("PROXIMA...", 20, 108),
                ]
            tela(linhas)
            utime.sleep_ms(1800)

        apagar_leds()
        tela([
            ("FIM DO QUIZ!", 12, 15),
            ("PONTUACAO", 20, 40),
            (str(pontos) + " DE " + str(TOTAL_RODADAS), 40, 60),
            ("A: REINICIAR", 8, 100),
        ])
        esperar_A()


# =====================================================================
# COMPOSITOR 4/4 - ritmo estilo Pozzoli
# =====================================================================
# Grade de tempo: 1 tempo (seminima) = 12 "ticks".
#   12 e divisivel por 2, 3, 4 e 6 -> binarios, tercinas e sextinas
#   convivem na mesma grade sem arredondar.
#   Colcheia = 6, semicolcheia = 3, tercina (de colcheia) = 4,
#   sextina (de semicolcheia) = 2.
# Compasso = 48 ticks; 5 compassos = 240 ticks.

BEAT_TICKS = 12
BAR_TICKS = 48
MAX_BARS = 5
TOTAL_TICKS = BAR_TICKS * MAX_BARS
BPM_MIN = 40
BPM_MAX = 200
bpm = 120                # escolhido ao entrar no compositor
BEAT_MS = 60000 // bpm
BAR_MS = BEAT_MS * 4

OCT_MIN = 3              # oitavas disponiveis: 3 a 6 (DO4 = 262 Hz)
OCT_MAX = 6

# (nome, duracao_ticks, grade_de_inicio, vigas, grupo_tuplet)
F_NOME, F_DUR, F_GRADE, F_VIGAS, F_GRUPO = 0, 1, 2, 3, 4
FIGURES = [
    ("SEMIBREVE", 48, 6, 0, 0),
    ("MINIMA", 24, 6, 0, 0),
    ("SEMINIMA", 12, 6, 0, 0),
    ("COLCHEIA", 6, 6, 1, 0),
    ("SEMICOLCHEIA", 3, 3, 2, 0),
    ("TERCINA", 4, 4, 1, 3),
    ("SEXTINA", 2, 2, 2, 6),
]

# Escala cromatica (sustenidos) + pausa
NOTES = [
    ("DO", 262), ("DO#", 277), ("RE", 294), ("RE#", 311),
    ("MI", 330), ("FA", 349), ("FA#", 370), ("SOL", 392),
    ("SOL#", 415), ("LA", 440), ("LA#", 466), ("SI", 494),
    ("PAUSA", 0),
]
REST = len(NOTES) - 1

# Layout do OLED
X0 = 28          # inicio do compasso (x)
PX = 2           # pixels por tick -> 96 px por compasso
LINE_Y = 62      # linha unica de ritmo (Pozzoli)
TOP = LINE_Y - 18  # topo das hastes

# Cada evento e [tick_inicial, indice_nota, indice_figura, oitava].
score = []
cursor_tick = 0
new_note = 0
new_oct = 4
new_figure = 2   # SEMINIMA


def nota_freq(note, octv):
    """Frequencia da nota na oitava (tabela NOTES esta na oitava 4)."""
    f = NOTES[note][1]
    if octv >= 4:
        return f << (octv - 4)
    return f >> (4 - octv)


def nome_nota(note, octv):
    if note == REST:
        return "PAUSA"
    return "%s%d" % (NOTES[note][0], octv)


def duration(event):
    return FIGURES[event[2]][F_DUR]


def event_at(tick):
    for event in score:
        if event[0] <= tick < event[0] + duration(event):
            return event
    return None


def check_insert(tick, fig):
    """Retorna None se pode inserir, ou a mensagem do motivo."""
    nome, length, grade, vigas, grupo = FIGURES[fig]
    if not (0 <= tick < TOTAL_TICKS):
        return "FORA DO LIMITE"
    if tick % grade:
        return "FORA DA GRADE"
    if tick % BAR_TICKS + length > BAR_TICKS:
        return "ESTOURA COMPASSO"
    if grupo and tick % BEAT_TICKS + length > BEAT_TICKS:
        return "ESTOURA TEMPO"
    for e in score:
        s = e[0]
        if tick < s + duration(e) and s < tick + length:
            return "POSICAO OCUPADA"
    # Nao mistura tercina/sextina com outra divisao no mesmo tempo
    b0 = (tick // BEAT_TICKS) * BEAT_TICKS
    b1 = ((tick + length - 1) // BEAT_TICKS + 1) * BEAT_TICKS
    for e in score:
        s = e[0]
        if s < b1 and b0 < s + duration(e):
            if FIGURES[e[2]][F_GRUPO] != grupo:
                return "NAO MISTURE"
    return None


def add_event(tick, note, fig, octv):
    msg = check_insert(tick, fig)
    if msg is not None:
        return msg
    score.append([tick, note, fig, octv])
    score.sort(key=lambda event: event[0])
    return None


def delete_event(tick):
    event = event_at(tick)
    if event is None:
        return None
    score.remove(event)
    return event


def next_tick(tick, g):
    ev = event_at(tick)
    if ev is not None:
        end = ev[0] + duration(ev)
    else:
        end = (tick // g + 1) * g
        ev2 = event_at(end)
        if ev2 is not None:
            end = ev2[0]
    if end >= TOTAL_TICKS:
        return ev[0] if ev is not None else tick
    return end


def prev_tick(tick, g):
    if tick <= 0:
        return 0
    ev = event_at(tick - 1)
    if ev is not None:
        return ev[0]
    t = ((tick - 1) // g) * g
    ev = event_at(t)
    if ev is not None:
        return ev[0]
    return t


def snap_cursor():
    """Alinha o cursor (em espaco livre) a grade da figura escolhida."""
    global cursor_tick
    g = FIGURES[new_figure][F_GRADE]
    t = cursor_tick - cursor_tick % g
    if event_at(t) is None:
        cursor_tick = t
        return
    t += g
    if t < TOTAL_TICKS and event_at(t) is None:
        cursor_tick = t


# ---------- desenho ----------

def head_w(length):
    if length >= 48:
        return 7
    if length <= 2:
        return 3
    return 5


def stem_x(event):
    return X0 + PX * (event[0] % BAR_TICKS) + head_w(duration(event)) - 1


def draw_head(xs, fig):
    length = FIGURES[fig][F_DUR]
    w = head_w(length)
    h = 3 if w == 3 else 4
    y = LINE_Y - (1 if h == 3 else 2)
    if length >= 24:
        oled.rect(xs, y, w, h, 1)
    else:
        oled.fill_rect(xs, y, w, h, 1)
    return xs + w - 1


def draw_rest(xs, fig):
    length = FIGURES[fig][F_DUR]
    vigas = FIGURES[fig][F_VIGAS]
    if length >= 48:
        oled.fill_rect(xs, LINE_Y + 1, 7, 3, 1)       # pausa de semibreve
    elif length >= 24:
        oled.fill_rect(xs, LINE_Y - 3, 5, 3, 1)       # pausa de minima
    elif length >= 12:
        oled.line(xs + 1, LINE_Y - 9, xs + 4, LINE_Y - 5, 1)   # seminima
        oled.line(xs + 4, LINE_Y - 5, xs + 1, LINE_Y - 1, 1)
        oled.line(xs + 1, LINE_Y - 1, xs + 4, LINE_Y + 3, 1)
    else:
        oled.line(xs + 3, LINE_Y - 8, xs + 1, LINE_Y + 3, 1)   # colcheia e menores
        oled.fill_rect(xs, LINE_Y - 7, 2, 2, 1)
        if vigas >= 2:
            oled.fill_rect(xs, LINE_Y - 3, 2, 2, 1)


def beam_run(run):
    n = len(run)
    xs = [stem_x(e) for e in run]
    if n == 1:
        beams = FIGURES[run[0][2]][F_VIGAS]
        for k in range(beams):
            oled.line(xs[0], TOP + 3 * k, xs[0] + 3, TOP + 3 * k + 3, 1)
        return
    oled.fill_rect(xs[0], TOP, xs[-1] - xs[0] + 1, 2, 1)
    for i in range(n):
        if FIGURES[run[i][2]][F_VIGAS] >= 2:
            nxt = i + 1 < n and FIGURES[run[i + 1][2]][F_VIGAS] >= 2
            prv = i > 0 and FIGURES[run[i - 1][2]][F_VIGAS] >= 2
            if nxt:
                oled.fill_rect(xs[i], TOP + 3, xs[i + 1] - xs[i] + 1, 2, 1)
            elif not prv:
                if i > 0:
                    oled.fill_rect(xs[i] - 3, TOP + 3, 4, 2, 1)
                else:
                    oled.fill_rect(xs[i], TOP + 3, 4, 2, 1)


def tuplet_mark(tup):
    first = tup[0]
    last = tup[-1]
    xa = X0 + PX * (first[0] % BAR_TICKS)
    xb = X0 + PX * ((last[0] % BAR_TICKS) + duration(last)) - 1
    oled.hline(xa, TOP - 4, xb - xa + 1, 1)
    oled.vline(xa, TOP - 4, 3, 1)
    oled.vline(xb, TOP - 4, 3, 1)
    oled.text(str(FIGURES[first[2]][F_GRUPO]), (xa + xb) // 2 - 4, TOP - 14)


def draw_groups(bar):
    b0 = bar * BAR_TICKS
    for beat in range(4):
        lo = b0 + beat * BEAT_TICKS
        hi = lo + BEAT_TICKS
        run = []
        tup = []
        for e in score:
            s = e[0]
            if s < lo:
                continue
            if s >= hi:
                break
            fig = FIGURES[e[2]]
            if fig[F_GRUPO]:
                tup.append(e)
            if fig[F_VIGAS] and e[1] != REST:
                if run and run[-1][0] + duration(run[-1]) != s:
                    beam_run(run)
                    run = []
                run.append(e)
            else:
                if run:
                    beam_run(run)
                    run = []
        if run:
            beam_run(run)
        if tup:
            tuplet_mark(tup)


def draw(bar, playing=False):
    oled.fill(0)
    oled.text("COMPASSO %d/%d" % (bar + 1, MAX_BARS), 0, 0)
    oled.text(("TOCANDO" if playing else "EDITOR") + " %d BPM" % bpm, 0, 10)
    if not playing:
        oled.text("X:NAV Y:NOTA", 0, 20)

    # Linha unica de ritmo, barras de compasso e numeracao dos tempos
    oled.hline(X0 - 3, LINE_Y, 101, 1)
    oled.vline(X0 - 3, LINE_Y - 20, 26, 1)
    oled.vline(X0 + 97, LINE_Y - 20, 26, 1)
    oled.text("4/4", 0, 58)
    for beat in range(4):
        oled.vline(X0 + 24 * beat, LINE_Y + 4, 3, 1)
        oled.text(str(beat + 1), X0 + 24 * beat, 70)

    # Figuras ritmicas (sem pauta, sem altura)
    for e in score:
        if e[0] // BAR_TICKS != bar:
            continue
        xs = X0 + PX * (e[0] % BAR_TICKS)
        if e[1] == REST:
            draw_rest(xs, e[2])
        else:
            sx = draw_head(xs, e[2])
            if duration(e) < 48:
                oled.vline(sx, TOP, LINE_Y - TOP, 1)
    draw_groups(bar)

    if playing:
        oled.text("OUCA A MELODIA", 0, 106)
        oled.show()
        return

    # Cursor: barra cheia = nota selecionada, vazada = espaco livre
    sel = event_at(cursor_tick)
    if cursor_tick // BAR_TICKS == bar:
        if sel is not None:
            s, length = sel[0], duration(sel)
        else:
            s, length = cursor_tick, FIGURES[new_figure][F_DUR]
        local = s % BAR_TICKS
        length = min(length, BAR_TICKS - local)
        xa = X0 + PX * local
        w = max(PX * length - 1, 3)
        if sel is not None:
            oled.fill_rect(xa, 80, w, 3, 1)
        else:
            oled.rect(xa, 80, w, 4, 1)

    if sel is None:
        oled.text("LIVRE:%s" % nome_nota(new_note, new_oct), 0, 94)
        oled.text("FIG:%s" % FIGURES[new_figure][F_NOME], 0, 105)
        oled.text("B:FIG A:+ C:>", 0, 117)
    else:
        oled.text("NOTA:%s" % nome_nota(sel[1], sel[3]), 0, 94)
        oled.text("DUR:%s" % FIGURES[sel[2]][F_NOME], 0, 105)
        oled.text("B:OIT SW:APAGA", 0, 117)
    oled.show()


def light_bar(bar, n):
    n = max(0, min(25, n))
    for k, physical in enumerate(LED_ORDER):
        pixels[physical] = COLORS[bar] if k < n else (0, 0, 0)
    pixels.write()


def play():
    if not score:
        message("INSIRA NOTAS")
        return
    last_bar = max((e[0] + duration(e) - 1) // BAR_TICKS for e in score)
    clear_lights()
    try:
        draw(0, playing=True)
        play_start = utime.ticks_ms()
        for bar in range(last_bar + 1):
            bar_start = utime.ticks_add(play_start, bar * BAR_MS)
            previous = None
            for step in range(BAR_TICKS):
                tick = bar * BAR_TICKS + step
                active = event_at(tick)
                if active is not previous:
                    buzzer.duty_u16(0)
                    if active is not None:
                        freq = nota_freq(active[1], active[3]) if active[1] != REST else 0
                        if freq:
                            utime.sleep_ms(8)   # separa notas repetidas
                            buzzer.freq(freq)
                            buzzer.duty_u16(16384)
                    previous = active
                # Pequeno respiro no fim de notas longas
                if (active is not None and duration(active) >= 12
                        and tick == active[0] + duration(active) - 1):
                    buzzer.duty_u16(0)
                # Troca de compasso na tela: depois de iniciar o som
                if step == 0 and bar > 0:
                    draw(bar, playing=True)
                light_bar(bar, (step + 1) * 25 // BAR_TICKS)
                target = utime.ticks_add(bar_start, (step + 1) * BAR_MS // BAR_TICKS)
                wait = utime.ticks_diff(target, utime.ticks_ms())
                if wait > 0:
                    utime.sleep_ms(wait)
            buzzer.duty_u16(0)
        utime.sleep_ms(400)
    finally:
        buzzer.duty_u16(0)
        clear_lights()


def tocar_curto(freq, ms=300):
    buzzer.freq(freq)
    buzzer.duty_u16(16384)
    utime.sleep_ms(ms)
    buzzer.duty_u16(0)


def pedir_bpm(valor):
    """Y: +-5, X: +-1, A ou SW confirma."""
    while True:
        oled.fill(0)
        oled.text("ANDAMENTO", 28, 8)
        oled.text("(BPM)", 44, 20)
        oled.fill_rect(24, 44, 80, 24, 1)
        txt = str(valor)
        oled.text(txt, 64 - 4 * len(txt), 52, 0)
        oled.text("Y: +-5   X: +-1", 4, 84)
        oled.text("A/SW: OK", 28, 100)
        oled.show()
        ev = ler_evento(((BTN_A, "OK"), (JOY_SW, "OK")))
        if ev == "CIMA":
            valor = min(BPM_MAX, valor + 5)
        elif ev == "BAIXO":
            valor = max(BPM_MIN, valor - 5)
        elif ev == "DIREITA":
            valor = min(BPM_MAX, valor + 1)
        elif ev == "ESQUERDA":
            valor = max(BPM_MIN, valor - 1)
        else:
            return valor


def pedir_oitava(note, octv):
    """Escolhe a oitava (3 a 6) ouvindo a nota. A confirma, B cancela.
    Retorna a oitava ou None se cancelado."""
    nome = NOTES[note][0]
    while True:
        oled.fill(0)
        oled.text("ESCOLHA OITAVA", 8, 0)
        oled.text("NOTA: " + nome, 20, 14)
        for k in range(OCT_MAX - OCT_MIN + 1):
            o = OCT_MAX - k
            y = 32 + 14 * k
            if o == octv:
                oled.fill_rect(24, y - 2, 80, 13, 1)
                oled.text("OITAVA %d" % o, 32, y, 0)
            else:
                oled.text("OITAVA %d" % o, 32, y)
        oled.text("Y:ESCOLHE", 0, 94)
        oled.text("A:OK B:VOLTA", 0, 106)
        oled.show()
        ev = ler_evento(((BTN_A, "OK"), (BTN_B, "CANCELA")))
        if ev in ("CIMA", "DIREITA"):
            octv = min(OCT_MAX, octv + 1)
        elif ev in ("BAIXO", "ESQUERDA"):
            octv = max(OCT_MIN, octv - 1)
        elif ev == "OK":
            return octv
        else:
            return None


def compositor():
    global cursor_tick, new_note, new_figure, new_oct
    global bpm, BEAT_MS, BAR_MS
    bpm = pedir_bpm(bpm)
    BEAT_MS = 60000 // bpm
    BAR_MS = BEAT_MS * 4
    score[:] = []
    cursor_tick = 0
    new_note = 0
    new_oct = 4
    new_figure = 2
    buzzer.duty_u16(0)
    clear_lights()
    print("Compositor: X navega | Y altera nota | B figura/oitava | A insere")
    print("C ouve | SW apaga | RESET volta ao menu")

    botoes = ((BTN_B, "FIGURA"), (BTN_A, "INSERIR"),
              (BTN_C, "TOCAR"), (JOY_SW, "APAGAR"))

    while True:
        draw(cursor_tick // BAR_TICKS)
        ev = ler_evento(botoes)
        g = FIGURES[new_figure][F_GRADE]

        if ev == "ESQUERDA":
            cursor_tick = prev_tick(cursor_tick, g)
        elif ev == "DIREITA":
            cursor_tick = next_tick(cursor_tick, g)
        elif ev in ("CIMA", "BAIXO"):
            delta = 1 if ev == "CIMA" else -1
            selected = event_at(cursor_tick)
            if selected is None:
                new_note = (new_note + delta) % len(NOTES)
            else:
                selected[1] = (selected[1] + delta) % len(NOTES)
        elif ev == "FIGURA":
            selected = event_at(cursor_tick)
            if selected is None:
                new_figure = (new_figure + 1) % len(FIGURES)
                snap_cursor()
            elif selected[1] == REST:
                message("PAUSA S/ OITAVA")
            else:
                novo = pedir_oitava(selected[1], selected[3])
                if novo is not None:
                    selected[3] = novo
        elif ev == "INSERIR":
            msg = check_insert(cursor_tick, new_figure)
            if msg is not None:
                message(msg)
            else:
                octv = new_oct
                if new_note != REST:
                    octv = pedir_oitava(new_note, new_oct)
                if octv is not None:
                    new_oct = octv
                    add_event(cursor_tick, new_note, new_figure, octv)
                    cursor_tick = next_tick(cursor_tick, FIGURES[new_figure][F_GRADE])
        elif ev == "APAGAR":
            removed = delete_event(cursor_tick)
            if removed is not None:
                cursor_tick = removed[0]
                new_note = removed[1]
                new_figure = removed[2]
                new_oct = removed[3]
            else:
                message("POSICAO VAZIA")
        elif ev == "TOCAR":
            play()


# =====================================================================
# PROGRAMA PRINCIPAL
# =====================================================================

if __name__ == "__main__":
    try:
        clear_lights()
        apagar_leds()
        if menu() == 0:
            quiz()
        else:
            compositor()
    finally:
        buzzer.duty_u16(0)
        apagar_leds()
        clear_lights()
