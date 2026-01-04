import numpy as np
from manim import *
from copy import deepcopy
from PIL import Image, ImageOps
from PIL import GifImagePlugin
from dataclasses import dataclass
GifImagePlugin.LOADING_STRATEGY = GifImagePlugin.LoadingStrategy.RGB_ALWAYS

@dataclass
class GifStatus:
    frame: int = 0
    time: float = 0
    def __deepcopy__(self, memo):
        return self
    
@dataclass
class VideoStatus:
    time: float = 0
    videoObject: cv2.VideoCapture = None
    def __deepcopy__(self, memo):
        return self

class GifImageMobject(ImageMobject):
    '''
    Following a discussion on Discord about animated GIF images.
    Parameters
    ----------
    filename
        the filename of the GIF image
    frame_duration
        (optional) overrides the frame duration given in the GIF file
    imageops
        (optional) possibility to include a PIL.ImageOps operation, e.g. 
        PIL.ImageOps.mirror
    https://discord.com/channels/581738731934056449/1126245755607339250/1126245755607339250
    2023-07-06 Uwe Zimmermann & Abulafia
    '''
    def __init__(self, filename=None, frame_duration=None, imageops=None, **kwargs):
        imageObject = Image.open(filename)
        self.filename = filename
        self._id = id(self)
        self.status = GifStatus()

        if not imageObject.is_animated:
            raise TypeError("file is not an animated GIF")      

        self.gifFrames = []
        self.nFrames = imageObject.n_frames
        for frame in range(imageObject.n_frames):
            imageObject.seek(frame)
            if imageops != None:
                self.gifFrames.append(ImageMobject(imageops(imageObject)))
            else:
                self.gifFrames.append(ImageMobject(imageObject))

            self.gifFrames[-1].duration = imageObject.info['duration'] if frame_duration==None else frame_duration

        self.current_image = self.gifFrames[0]
        super().__init__(self.gifFrames[0].get_pixel_array(), **kwargs)
        self.pixel_array = np.zeros(self.pixel_array.shape)
        self.add(self.current_image)
        self.current_image.add_updater(self.gifUpdater)

    # changed for FadeIn compatibility by KeJunMao, 2024-11-24
    def set_opacity(self, alpha: float):
        super().set_opacity(alpha)
        for frame in self.gifFrames:
            frame.set_opacity(alpha)

    def gifUpdater(self, mobj, dt):
        if dt == 0:
            return
        status = self.status
        status.time += 1000*dt 
        if status.time > self.gifFrames[status.frame].duration:
            status.time = 0
            mobj.pixel_array = self.gifFrames[status.frame].pixel_array
            status.frame = (status.frame + 1) % self.nFrames

class VideoMobject(ImageMobject):
    '''
    Following a discussion on Discord about animated GIF images.
    Modified for videos
    Parameters
    ----------
    filename
        the filename of the video file
    imageops
        (optional) possibility to include a PIL.ImageOps operation, e.g.
        PIL.ImageOps.mirror
    speed
        (optional) speed-up/slow-down the playback
    loop
        (optional) replay the video from the start in an endless loop
    https://discord.com/channels/581738731934056449/1126245755607339250/1126245755607339250
    2023-07-06 Uwe Zimmermann & Abulafia
    2024-03-09 Uwe Zimmermann
    '''
    def __init__(self, filename=None, imageops=None, speed=1.0, loop=False, **kwargs):
        self.filename = filename
        self.imageops = imageops
        self.speed    = speed
        self.loop     = loop
        self._id = id(self)
        self.status = VideoStatus()
        self.status.videoObject = cv2.VideoCapture(filename)

        self.status.videoObject.set(cv2.CAP_PROP_POS_FRAMES, 1)
        ret, frame = self.status.videoObject.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)            
            img = Image.fromarray(frame)

            if imageops != None:
                img = imageops(img)
        else:
            img = Image.fromarray(np.uint8([[63, 0, 0, 0], [0, 127, 0, 0], [0, 0, 191, 0], [0, 0, 0, 255]]))
        super().__init__(img, **kwargs)
        if ret:
            self.add_updater(self.videoUpdater)

    def videoUpdater(self, mobj, dt):
        if dt == 0:
            return
        status = self.status
        status.time += 1000*dt*mobj.speed
        self.status.videoObject.set(cv2.CAP_PROP_POS_MSEC, status.time)
        ret, frame = self.status.videoObject.read()
        if (ret == False) and self.loop:
            status.time = 0
            self.status.videoObject.set(cv2.CAP_PROP_POS_MSEC, status.time)
            ret, frame = self.status.videoObject.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # needed here?        
            img = Image.fromarray(frame)

            if mobj.imageops != None:
                img = mobj.imageops(img)
            mobj.pixel_array = change_to_rgba_array(
                np.asarray(img), mobj.pixel_array_dtype
            )

class Scenery(MovingCameraScene):
    def construct(self):  
        CAM = self.camera.frame
        # COLORS
        WHITE_G = color_gradient([WHITE, WHITE], 2)
        YEBLUE_G = color_gradient([ManimColor.from_hex("#FFED95"), ManimColor.from_hex("#16E3F9")], 200)
        AXCOL = color_gradient([ManimColor.from_hex("#FFED95"), ManimColor.from_hex("#16E3F9")], 200)
        YELL_G = color_gradient([ManimColor.from_hex("#FEFE99"), ManimColor.from_hex("#FFC655")], 200)
        GREEN_G = color_gradient([ManimColor.from_hex("#BFFF97"), ManimColor.from_hex("#00C849")], 200)
        RED_G = color_gradient([ManimColor.from_hex("#FF7490"), ManimColor.from_hex("#FF0033")], 200)
    
        tex_marks = TexTemplate()
        tex_marks.add_to_preamble(r'\usepackage{pifont}')

        def TexGen(string, font_sz=50, col=WHITE_G, isMath=False, stroke_w=1.0):
            if not isMath:
                return Tex(fr'{string}', font_size=font_sz).set_color(col).set_stroke(color=average_color(col[0], col[-1]), width=stroke_w)
            else:
                return MathTex(fr'{string}', font_size=font_sz).set_color(col).set_stroke(color=average_color(col[0], col[-1]), width=stroke_w)
            
        def DrawTxt(txt, stroke_w=2.0):
            return DrawBorderThenFill(txt, stroke_color=txt.get_stroke_colors(), stroke_width=stroke_w, run_time=1)
        
        def BounceIn(mobjects) -> Animation:
            bounce_anims = []
            for mob in mobjects:
                bounce_anims.append(GrowFromCenter(mob, rate_func=rate_functions.ease_out_back, run_time=0.5))
            return bounce_anims
        
        def RectAroundImage(img):
            rect1 = SurroundingRectangle(img, corner_radius=0.2, color=WHITE, buff=0)
            rect2 = SurroundingRectangle(rect1, corner_radius=0.2, color=WHITE, buff=0.01)
            rect3 = SurroundingRectangle(rect2, corner_radius=0.2, color=WHITE, buff=0.01)
            rect4 = SurroundingRectangle(rect3, corner_radius=0.2, color=WHITE, buff=0.01)
            rect5 = SurroundingRectangle(rect4, corner_radius=0.2, color=BLACK, buff=0.01)
            rect6 = SurroundingRectangle(rect5, corner_radius=0.2, color=BLACK, buff=0.01)
            rect7 = SurroundingRectangle(rect6, corner_radius=0.2, color=BLACK, buff=0.01)
            rect8 = SurroundingRectangle(rect7, corner_radius=0.2, color=BLACK, buff=0.01)
            rect9 = SurroundingRectangle(rect8, corner_radius=0.2, color=BLACK, buff=0.01)
            rect10 = SurroundingRectangle(rect9, corner_radius=0.2, color=BLACK, buff=0.01)
            return VGroup([rect1, rect2, rect3, rect4, rect5, rect6, rect7, rect8, rect9, rect10])
        
        def play_intro():
            pin1 = ImageMobject('pin.png').shift(2.5*UP+2*LEFT)
            pin1.height = 2
            pin2 = deepcopy(pin1).shift(4*RIGHT)
            clock = ImageMobject(r'clock.png')
            clock.height = 2
            pin_line = DashedLine(start=[-2, 1.5, 0], end=[2, 1.5, 0], dash_length=0.2).set_stroke(width=6)
            pin_line.add_updater(lambda mob: mob.put_start_and_end_on(start=[-2, 1.5, 0], end=[pin2.get_x(), 1.5, 0]))
            self.play(BounceIn(pin1), Create(pin_line))
            self.play(BounceIn(pin2))
            self.play(pin2.animate.move_to(pin1))
            self.remove(pin_line)
            frac_line = Line(start=[-2.75, 0, 0], end=[-1.35, 0, 0]).set_stroke(width=4)
            zero_m = TexGen(r'0 m', isMath=False, font_sz=80).next_to(frac_line, UP, buff=0.33)
            self.play(DrawTxt(zero_m))
            zero_s = TexGen(r'0 s', isMath=False, font_sz=80).next_to(frac_line, DOWN)
            self.play(BounceIn(clock.move_to(pin1).shift(5*DOWN)))
            self.play(DrawTxt(zero_s))
            self.wait()
            self.play(BounceIn(frac_line))
            eq_2ms = TexGen(r'= 2 \frac{\textup{m}}{\textup{s}}', isMath=True, font_sz=70).next_to(frac_line, RIGHT, buff=0.3).shift(0.03*DOWN)
            self.play(DrawTxt(eq_2ms))
            zero_div_eq_2 = TexGen(r'\frac{0}{0}=2', isMath=True, font_sz=70).to_edge(UL, buff=1)
            proof = TexGen(r'\textit{Beweis.}', isMath=False, font_sz=70).next_to(zero_div_eq_2, 3*DOWN, aligned_edge=LEFT)
            self.play(FadeOut(pin1, pin2, clock), run_time=0.5)
            self.play(ReplacementTransform(VGroup(zero_m, frac_line, zero_s, eq_2ms), zero_div_eq_2))
            self.play(DrawTxt(proof))
            zero_div_zero = TexGen(r'\frac{0}{0}', isMath=True, font_sz=70).next_to(proof, 2*DOWN, aligned_edge=LEFT)
            self.wait()
            self.play(DrawTxt(zero_div_zero))
            first_term = TexGen(r'= \frac{1-1}{1-1}', isMath=True, font_sz=70).next_to(zero_div_zero, RIGHT, buff=0.3)
            second_term = TexGen(r'= \frac{1^2-1^2}{1^2-1^2}', isMath=True, font_sz=70).next_to(zero_div_zero, RIGHT, buff=0.3).shift(0.07*UP)
            bino = TexGen(r'a^2-b^2 = (a+b)\cdot(a-b)', isMath=True, font_sz=50)
            self.play(DrawTxt(first_term))
            self.wait()
            self.play(ReplacementTransform(first_term, second_term))
            self.wait()
            self.play(DrawTxt(bino.move_to(second_term).to_edge(RIGHT, buff=1)))
            self.wait()
            eq = TexGen(r'=', isMath=True, font_sz=70).next_to(second_term, RIGHT, buff=0.3).shift(0.12*DOWN)
            thrid_term1 = TexGen(r'(1+1)\cdot(1-1)', isMath=True, font_sz=70)
            thrid_term_frac = Line(start=[0, 0, 0], end=[thrid_term1.width, 0, 0]).set_stroke(width=4).next_to(eq, RIGHT, buff=0.3)
            thrid_term2 = TexGen(r'1\cdot(1-1)', isMath=True, font_sz=70).next_to(thrid_term_frac, DOWN, buff=0.13)
            self.play(DrawTxt(eq), ReplacementTransform(bino, thrid_term1.next_to(thrid_term_frac, UP, buff=0.12)))
            self.wait()
            self.play(BounceIn(thrid_term_frac))
            self.wait()
            self.play(DrawTxt(thrid_term2))
            self.wait()
            ref_txt = TexGen(r'(1-1)', isMath=True, font_sz=70)
            r_line1 = Line(start=ref_txt.get_corner(DL), end=ref_txt.get_corner(UR)).set_color(YEBLUE_G).set_stroke(color=YEBLUE_G, width=5).move_to(thrid_term1, aligned_edge=RIGHT)
            r_line2 =  deepcopy(r_line1).move_to(thrid_term2, aligned_edge=RIGHT)
            self.play(BounceIn(r_line1), BounceIn(r_line2))
            eq_2 = TexGen(r'= 2', isMath=True, font_sz=70).next_to(thrid_term_frac, RIGHT, buff=0.3).shift(0.06*UP)
            self.wait()
            self.play(DrawTxt(eq_2))
            qed = TexGen(r'\textit{q.e.d.}', isMath=False, font_sz=70).next_to(eq_2, 2.7*DOWN).to_edge(RIGHT, buff=1)
            self.play(DrawTxt(qed))
            self.wait()
            marks = TexGen(r'?!', isMath=False, font_sz=200, col=RED_G).next_to(zero_div_eq_2, RIGHT, buff=1)
            xmark = Tex(r'\ding{55}', tex_template=tex_marks, font_size=130).set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1]), width=2).move_to([-5.95, 1.8, 0])
            self.play(DrawTxt(marks))
            self.wait()
            self.play(ReplacementTransform(marks, xmark)) 
            self.play(FadeOut(zero_div_zero, second_term, thrid_term1, thrid_term2, thrid_term_frac, proof, qed, r_line1, r_line2, eq_2, eq))
            self.wait()
            notallowed = TexGen(r"NICHT\\ERLAUBT!", font_sz=120, col=RED_G).set_z_index(-1)
            self.play(DrawTxt(notallowed))
            self.wait()
            self.play(xmark.animate.move_to(notallowed).scale(5))
            self.wait()
            self.play(FadeOut(zero_div_eq_2, xmark, notallowed))

        def play_math():
            soup = ImageMobject(r'suppe.png').shift(0.6*DOWN)
            soup.height = 3
            self.play(BounceIn(soup))
            axioms_arr = Arrow(start=[0, 2, 0], end=[0, 1.2, 0], buff=0, tip_shape=StealthTip, stroke_width=10)
            theorems_arr = deepcopy(axioms_arr).rotate(PI/2.8, about_point=ORIGIN)
            definitions_arr = deepcopy(axioms_arr).rotate(-PI/2.8, about_point=ORIGIN)
            theorems = TexGen(r'Theoreme', isMath=False, font_sz=70).move_to([-3.9, 1.2, 0])
            definitions = TexGen(r'Definitionen', isMath=False, font_sz=70).move_to([4, 1.2, 0])
            axioms = TexGen(r'Axiome', isMath=False, font_sz=70).shift(3.2*UP)
            self.wait()
            self.play(DrawTxt(theorems), Create(theorems_arr))
            self.wait()
            eq_statement = TexGen(r'$\widehat{=}$', font_sz=40).next_to(theorems, DOWN, aligned_edge=LEFT)
            statement1 = TexGen(r'wahre Aussagen,', font_sz=40).next_to(eq_statement, RIGHT, buff=0.15).shift(0.08*DOWN)
            statement2 = TexGen(r'mit Beweis', font_sz=40).next_to(statement1, DOWN, aligned_edge=LEFT, buff=0.1)
            statement = VGroup(eq_statement, statement1, statement2)
            self.play(DrawTxt(statement))
            self.wait()
            eq_meaning = TexGen(r'$\widehat{=}$', font_sz=40).next_to(definitions, DOWN, aligned_edge=LEFT)
            meaning1 = TexGen(r'Bedeutung Begriffe,', font_sz=40).next_to(eq_meaning, RIGHT, buff=0.15).shift(0.08*DOWN)
            meaning2 = TexGen(r'Ausdrücke', font_sz=40).next_to(meaning1, DOWN, aligned_edge=LEFT, buff=0.1)
            meaning = VGroup(eq_meaning, meaning1, meaning2)
            self.play(DrawTxt(definitions), Create(definitions_arr))
            self.wait()
            self.play(DrawTxt(meaning))
            self.wait()
            eq_ax = TexGen(r'$\widehat{=}$', font_sz=40)
            ax1 = TexGen(r'wahre Aussagen, ohne Beweis', font_sz=40).next_to(eq_ax, RIGHT, buff=0.15).shift(0.08*DOWN)
            ax_statement = VGroup(eq_ax, ax1).next_to(axioms, DOWN)
            self.play(DrawTxt(axioms), Create(axioms_arr))
            self.wait()
            self.play(DrawTxt(ax_statement))
            self.wait()
            self.play(FadeOut(ax_statement, soup, theorems, theorems_arr, definitions, definitions_arr, axioms_arr, statement, meaning), axioms.animate.set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1])))
            three = TexGen(r'3', isMath=True, font_sz=300)
            self.wait()
            self.play(DrawTxt(three))
            self.wait()
            hand = ImageMobject('hand.png')
            hand.height = 2
            hand.move_to(three).shift(0.83*DOWN+0.21*LEFT).set_z_index(-1)
            self.play(FadeIn(hand, target_position=[0, -6, 0]))
            self.wait()
            self.play(FadeOut(hand))
            rom_three = TexGen(r'III', isMath=False, font_sz=300)
            word_three = TexGen(r'drei', isMath=False, font_sz=220)
            self.wait()
            self.play(ReplacementTransform(three, rom_three), run_time=0.5)
            self.wait()
            self.play(ReplacementTransform(rom_three, word_three))
            self.wait()
            self.play(FadeOut(word_three))
            piraha = ImageMobject('piraha.jpg').set_z_index(-1)
            piraha.height = 4
            rect_around_piraha = RectAroundImage(piraha)
            pirect = Group(piraha, rect_around_piraha).move_to([-3, -0.8,  0])
            piraha_tribe = TexGen(r'Pirahã Stamm (Brasilien)', isMath=False, font_sz=40).next_to(pirect, UP, buff=0.18)
            self.play(FadeIn(pirect, target_position=[-3, -6, 0]))
            self.play(DrawTxt(piraha_tribe))
            self.wait()
            eq_sign1 = TexGen(r'$\widehat{=}$', isMath=False, font_sz=60).move_to([3.2, 0, 0])
            eq_sign2 = deepcopy(eq_sign1).next_to(eq_sign1, DOWN)
            eq_sign3 = deepcopy(eq_sign1).next_to(eq_sign2, DOWN)
            hoi_one = TexGen(r'hói', isMath=False, font_sz=60).next_to(eq_sign1, LEFT, buff=0.2)
            hoi_two = TexGen(r'hoí', isMath=False, font_sz=60).next_to(eq_sign2, LEFT, buff=0.2)
            baagiso = TexGen(r'baagiso', isMath=False, font_sz=60).next_to(eq_sign3, LEFT, buff=0.2)
            one = TexGen(r'``eins"', isMath=False, font_sz=60).next_to(eq_sign1, RIGHT, buff=0.2)
            two = TexGen(r'``zwei"', isMath=False, font_sz=60).next_to(eq_sign2, RIGHT, buff=0.2)
            many = TexGen(r'``viele"', isMath=False, font_sz=60).next_to(eq_sign3, RIGHT, buff=0.2)
            few = TexGen(r'``wenige"', isMath=False, font_sz=60).next_to(eq_sign1, RIGHT, buff=0.2)
            some = TexGen(r'``einige"', isMath=False, font_sz=60).next_to(eq_sign2, RIGHT, buff=0.2)
            self.play(DrawTxt(hoi_one), DrawTxt(eq_sign1), DrawTxt(one))
            self.play(DrawTxt(hoi_two), DrawTxt(eq_sign2), DrawTxt(two))
            self.play(DrawTxt(baagiso), DrawTxt(eq_sign3), DrawTxt(many))
            self.wait()
            self.play(ReplacementTransform(one, few), ReplacementTransform(two, some))
            self.wait()
            self.play(FadeOut(few, some, many, eq_sign1, eq_sign2, eq_sign3, pirect, hoi_one, hoi_two, baagiso, piraha_tribe))
            natural_num = TexGen(r'``Natürliche" Zahlen\\$1, 2, 3, \ldots$', isMath=False, font_sz=50)
            natural_num2 = TexGen(r'\mathbb{N}?', isMath=True, font_sz=50).shift(2*UP).to_edge(LEFT, buff=1.6)
            peano = ImageMobject('peano.png')
            peano.height = 3
            peano.next_to(natural_num2, 2.8*DOWN)
            peano_name = TexGen(r'Giuseppe Peano\\(1858--1932)', isMath=False, font_sz=40).next_to(peano, DOWN, buff=0.15)
            self.play(DrawTxt(natural_num))
            self.wait()
            self.play(ReplacementTransform(natural_num, natural_num2))
            self.wait()
            self.play(BounceIn(peano), DrawTxt(peano_name))
            self.wait()
            ding1 = Tex(r'\ding{182}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).move_to([-2.6, 0.8, 0])
            ding2 = Tex(r'\ding{183}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).next_to(ding1, 1.8*DOWN)
            ding3 = Tex(r'\ding{184}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).next_to(ding2, 1.8*DOWN)
            ding4 = Tex(r'\ding{185}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).next_to(ding3, 1.8*DOWN)
            ding5 = Tex(r'\ding{186}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).next_to(ding4, 1.8*DOWN)
            dinger = VGroup(ding1, ding2, ding3, ding4, ding5)
            A1 = TexGen(r'``1 ist eine natürliche Zahl."', isMath=False, font_sz=40, col=AXCOL).next_to(ding1)
            A2_1 = TexGen(r'``Jede natürliche Zahl $n$ hat eine natürliche', isMath=False, font_sz=40, col=AXCOL).next_to(A1, DOWN, aligned_edge=LEFT, buff=0.5)
            A2_2 = TexGen(r'Zahl $S(n)$ als Nachfolger."', isMath=False, font_sz=40, col=AXCOL).next_to(A2_1, DOWN, aligned_edge=LEFT, buff=0.1).shift(0.05*RIGHT)
            A2 = VGroup(A2_1, A2_2).next_to(ding2)
            A3 = TexGen(r'``1 ist kein Nachfolger einer natürlichen Zahl."', isMath=False, font_sz=40, col=AXCOL).next_to(ding3)
            A4_1 = TexGen(r'``Sind die Nachfolger zweier Zahlen gleich,', isMath=False, font_sz=40, col=AXCOL).next_to(A3, DOWN, aligned_edge=LEFT, buff=0.5)
            A4_2 = TexGen(r'so müssen diese Zahlen selbst gleich sein."', isMath=False, font_sz=40, col=AXCOL).next_to(A4_1, DOWN, aligned_edge=LEFT, buff=0.1).shift(0.05*RIGHT)
            A4 = VGroup(A4_1, A4_2).next_to(ding4)
            A5 = TexGen(r'``Induktionsprinzip $\ldots$"', isMath=False, font_sz=40, col=AXCOL).next_to(ding5)
            n1 = TexGen(r'1', isMath=False).next_to(natural_num2, buff=0.75)
            n2 = TexGen(r', $S(1)$', isMath=False).next_to(n1, buff=0.07).shift(0.04*DOWN)
            n3 = TexGen(r', $S(S(1))$', isMath=False).next_to(n2, buff=0.06)
            n4 = TexGen(r', $S(S(S(1)))$, $\ldots$', isMath=False).next_to(n3, buff=0.06)
            open_br = TexGen(r'\{', isMath=True).next_to(n1, LEFT, buff=0.06)
            n2_new = TexGen(r', 2', isMath=False).next_to(n1, buff=0.07).shift(0.04*DOWN)
            n3_new = TexGen(r', 3', isMath=False).next_to(n2_new, buff=0.06)
            n4_new = TexGen(r', 4, $\ldots$', isMath=False).next_to(n3_new, buff=0.06)
            closed_br = TexGen(r'\}', isMath=True).next_to(n4_new, buff=0.06).set_y(open_br.get_y())
            natural_num3 = TexGen(r'\mathbb{N}=', isMath=True, font_sz=50).move_to(natural_num2, aligned_edge=LEFT)
            self.play(LaggedStart(*(FadeIn(ding, target_position=peano.get_center()) for ding in dinger)))
            self.wait()
            self.play(FadeIn(A1, target_position=peano.get_center()+[A1.width/2-1, 0, 0]))
            self.wait()
            self.play(DrawTxt(n1))
            self.wait()
            self.play(FadeIn(A2, target_position=peano.get_center()+[A2.width/2-1, 0, 0]))
            self.wait()
            self.play(DrawTxt(n2))
            self.wait()
            self.play(DrawTxt(n3))
            self.play(DrawTxt(n4))
            self.wait()
            self.play(FadeIn(A3, target_position=peano.get_center()+[A3.width/2-1, 0, 0]))
            self.wait()
            self.play(DrawTxt(open_br))
            self.wait()
            self.play(FadeIn(A4, target_position=peano.get_center()+[A4.width/2-1, 0, 0]))
            self.wait()
            self.play(ReplacementTransform(n2, n2_new), ReplacementTransform(n3, n3_new), ReplacementTransform(n4, n4_new))
            self.wait()
            self.play(FadeIn(A5, target_position=peano.get_center()+[A5.width/2-1, 0, 0]))
            self.wait()
            self.play(DrawTxt(closed_br))
            self.play(ReplacementTransform(natural_num2, natural_num3))
            self.wait()
            ding_c1 = Tex(r'\ding{108}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2)
            ding_c2 = deepcopy(ding_c1).next_to(ding_c1, buff=0.1)
            ding_c3 = deepcopy(ding_c1).next_to(ding_c2, buff=0.1)
            ding_c4 = deepcopy(ding_c1).next_to(ding_c3, buff=0.1)
            ding_c5 = deepcopy(ding_c1).next_to(ding_c4, buff=0.1)
            dings = VGroup(ding_c1, ding_c2, ding_c3, ding_c4, ding_c5).move_to([-3, 1, 0])
            self.play(FadeOut(peano, peano_name, natural_num3, A1, A2, A3, A4, A5, open_br, closed_br, n1, n2_new, n3_new, n4_new))
            self.play(ReplacementTransform(ding1, ding_c1), ReplacementTransform(ding2, ding_c2), ReplacementTransform(ding3, ding_c3), ReplacementTransform(ding4, ding_c4), ReplacementTransform(ding5, ding_c5))
            world = ImageMobject('world.png')
            world.height = 3
            self.play(BounceIn(world.next_to(dings, DOWN, buff=1)))
            self.wait()
            ding_n1 = Tex(r'\ding{74}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2)
            ding_n2 = deepcopy(ding_n1).next_to(ding_n1, buff=0.1)
            ding_n3 = deepcopy(ding_n1).next_to(ding_n2, buff=0.1)
            ding_n4 = deepcopy(ding_n1).next_to(ding_n3, buff=0.1)
            ding_n5 = deepcopy(ding_n1).next_to(ding_n4, buff=0.1)
            dings_n = VGroup(ding_n1, ding_n2, ding_n3, ding_n4, ding_n5).move_to([3, 1, 0])
            r_arr = TexGen(r'\rightarrow', isMath=True, font_sz=100).shift(1*UP)
            self.play(BounceIn(dings_n), DrawTxt(r_arr))
            self.play(world.animate.next_to(dings_n, DOWN, buff=1))
            self.wait()
            minimal = TexGen(r'minimal', isMath=False, font_sz=50).next_to(dings_n, UP)
            contra = TexGen(r'keine Widersprüche', isMath=False, font_sz=50).next_to(dings_n, UP)
            meaningful = TexGen(r'sinnvoll', isMath=False, font_sz=50).next_to(dings_n, UP)
            self.play(DrawTxt(minimal))
            self.play(ShrinkToCenter(ding_n1), ShrinkToCenter(ding_n5), run_time=0.5)
            self.wait()
            self.play(ReplacementTransform(minimal, contra))
            self.wait()
            self.play(ReplacementTransform(contra, meaningful))
            self.wait()
            self.play(FadeOut(dings, ding_n2, ding_n3, ding_n4, r_arr, meaningful, world, axioms))

        def play_zero():
            ding1 = Tex(r'\ding{182}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).shift(2.2*UP).to_edge(LEFT, buff=0.5)
            ding2 = Tex(r'\ding{183}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).next_to(ding1, DOWN)
            ding3 = Tex(r'\ding{184}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).next_to(ding2, DOWN)
            ding4 = Tex(r'\ding{185}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).next_to(ding3, DOWN)
            ding5 = Tex(r'\ding{186}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2).next_to(ding4, DOWN)
            dings = VGroup(ding1, ding2, ding3, ding4, ding5)
            asso = TexGen(r'Assoziativität:', isMath=False, font_sz=40, col=AXCOL).next_to(ding1)
            commu = TexGen(r'Kommutativität:', isMath=False, font_sz=40, col=AXCOL).next_to(ding2)
            ident = TexGen(r'Neutrales Elem.:', isMath=False, font_sz=40, col=AXCOL).next_to(ding3)
            invs = TexGen(r'Inversen:', isMath=False, font_sz=40, col=AXCOL).next_to(ding4)
            dist = TexGen(r'Distributivität:', isMath=False, font_sz=40, col=AXCOL).next_to(ding5)
            asso_a = TexGen(r'a+(b+c) = (a+b)+c', isMath=True, font_sz=40, col=AXCOL).next_to(asso, buff=1)
            commu_a = TexGen(r'a+b = b+a', isMath=True, font_sz=40, col=AXCOL).next_to(commu).set_x(asso_a.get_x())
            ident_a = TexGen(r'a+0=a', isMath=True, font_sz=40, col=AXCOL).next_to(commu_a, DOWN, aligned_edge=LEFT).set_y(ident.get_y())
            invs_a = TexGen(r'a+(-a)=0', isMath=True, font_sz=40, col=AXCOL).next_to(ident_a, DOWN, aligned_edge=RIGHT).set_y(invs.get_y())
            asso_m = TexGen(r'a \cdot (b \cdot c) = (a \cdot b) \cdot c', isMath=True, font_sz=40, col=AXCOL).next_to(asso_a, buff=1)
            commu_m = TexGen(r'a \cdot b = b \cdot a', isMath=True, font_sz=40, col=AXCOL).next_to(commu).set_x(asso_m.get_x())
            ident_m = TexGen(r'a \cdot 1 = a', isMath=True, font_sz=40, col=AXCOL).next_to(commu_m, DOWN, aligned_edge=LEFT).set_y(ident.get_y())
            invs_m = TexGen(r'a \cdot a^{-1} = 1', isMath=True, font_sz=40, col=AXCOL).next_to(ident_m, DOWN, aligned_edge=RIGHT).set_y(invs.get_y())
            plus = TexGen(r'+', isMath=True, font_sz=90).next_to(asso_a, UP, buff=0.5)
            cdot = TexGen(r'\cdot', isMath=True, font_sz=90).next_to(asso_m, UP).set_y(plus.get_y())
            dist_am = TexGen(r'a \cdot (b+c) = a \cdot b + a \cdot c', isMath=True, font_sz=40, col=AXCOL).next_to(dist).set_x(VGroup(plus, cdot).get_center()[0])
            addition = TexGen(r'Addition', isMath=False, font_sz=50)
            und = TexGen(r'\&', isMath=False, font_sz=50).next_to(addition)
            multiplication = TexGen(r'Multiplikation', isMath=False, font_sz=50).next_to(und, aligned_edge=UP)
            VGroup(addition, und, multiplication).move_to(ORIGIN).set_y(plus.get_y())
            sixminus = TexGen(r'6 - 2 = 4', isMath=True, font_sz=50).shift(2.5*DOWN)
            sixminus2 = TexGen(r'6 + (-2) = 4', isMath=True, font_sz=50).move_to(sixminus, aligned_edge=LEFT)
            sixdiv = TexGen(r'\frac{6}{2}=3', isMath=True, font_sz=50).shift(2.5*DOWN)
            sixdiv2 = TexGen(r'6 \cdot 2^{-1}=3', isMath=True, font_sz=50).move_to(sixdiv, aligned_edge=UL)
            aneq0 = TexGen(r'a \neq 0', isMath=True, font_sz=40, col=RED_G).next_to(invs_m, buff=0.5).shift(0.07*DOWN)
            self.play(DrawTxt(addition), DrawTxt(multiplication), DrawTxt(und))
            self.wait()
            self.play(ReplacementTransform(addition, plus), ReplacementTransform(multiplication, cdot), FadeOut(und, run_time=0.1))
            self.play(LaggedStartMap(BounceIn, dings, run_time=1.5))
            self.wait()
            self.play(DrawTxt(asso), DrawTxt(asso_a), DrawTxt(asso_m), DrawTxt(commu), DrawTxt(commu_a), DrawTxt(commu_m))
            self.wait()
            self.play(DrawTxt(ident))
            self.wait()
            self.play(DrawTxt(ident_a))
            self.wait()
            self.play(DrawTxt(ident_m))
            self.wait()
            self.play(DrawTxt(invs))
            self.wait()
            self.play(DrawTxt(invs_a))
            self.wait()
            self.play(DrawTxt(sixminus))
            self.wait()
            self.play(ReplacementTransform(sixminus, sixminus2))
            self.wait()
            self.play(FadeOut(sixminus2))
            self.play(DrawTxt(invs_m))
            self.wait()
            self.play(DrawTxt(sixdiv))
            self.wait()
            self.play(ReplacementTransform(sixdiv, sixdiv2))
            self.wait()
            self.play(FadeOut(sixdiv2))
            self.play(DrawTxt(aneq0))
            self.wait()
            self.play(DrawTxt(dist), DrawTxt(dist_am))
            self.wait()
            self.play(ShrinkToCenter(aneq0))
            self.wait()
            z1 = TexGen(r'0^{-1}', isMath=True, font_sz=50).shift(2.5*DOWN)
            self.play(DrawTxt(z1))
            self.wait()
            invs_m.save_state()
            self.play(invs_m.animate.scale(1.3).set_color(YELL_G).set_stroke(color=average_color(YELL_G[0], YELL_G[-1])))
            z2 = TexGen(r'0 \cdot 0^{-1} = 1', isMath=True, font_sz=50).move_to(z1)
            self.wait()
            self.play(ReplacementTransform(z1, z2))
            self.wait()
            self.play(Restore(invs_m), z2.animate.to_edge(LEFT, buff=0.5))
            self.wait()
            z3 = TexGen(r'0 \cdot 0^{-1} =', isMath=True, font_sz=50).shift(2.5*DOWN+1.5*LEFT)
            bff = 0.3
            scl = 1.2
            z4 = TexGen(r'?', isMath=True, font_sz=50).next_to(z3, buff=bff, aligned_edge=DOWN)
            self.play(DrawTxt(z3), DrawTxt(z4))
            self.wait()
            z5_1 = TexGen(r'0 \cdot 0^{-1} +', isMath=True, font_sz=50).next_to(z3, buff=bff)
            z5_2 = TexGen(r'0', isMath=True, font_sz=50).next_to(z5_1, buff=0.15, aligned_edge=DOWN).shift(0.02*UP)
            z5 = VGroup(z5_1, z5_2)
            ident_a.save_state()
            self.play(ident_a.animate.scale(scl).set_color(YELL_G).set_stroke(color=average_color(YELL_G[0], YELL_G[-1])))
            self.play(ReplacementTransform(z4, z5))
            self.wait()
            brk = TexGen(r'(\phantom{0\cdot 0^{-1} + (-0 \cdot 0^{-1})})', isMath=True, font_sz=50).next_to(z5_1, buff=0.15).shift(0.075*DOWN)
            z6_1 = TexGen(r'0 \cdot 0^{-1}', isMath=True, font_sz=50)
            z6_2 = TexGen(r'+ (-0 \cdot 0^{-1})', isMath=True, font_sz=50).next_to(z6_1, buff=0.15).shift(0.06*DOWN)
            z6 = VGroup(z6_1, z6_2).move_to(brk, aligned_edge=DOWN)
            self.play(Restore(ident_a))
            invs_a.save_state()
            self.play(invs_a.animate.scale(scl).set_color(YELL_G).set_stroke(color=average_color(YELL_G[0], YELL_G[-1])))
            self.wait()
            self.play(ReplacementTransform(z5_2, VGroup(brk, z6)))
            self.wait()
            self.play(Restore(invs_a))
            asso_a.save_state()
            self.play(asso_a.animate.scale(scl).set_color(YELL_G).set_stroke(color=average_color(YELL_G[0], YELL_G[-1])))
            self.wait()
            brk2 = TexGen(r'(\phantom{0 \cdot 0^{-1} + 0 \cdot 0^{-1}})', isMath=True, font_sz=50).next_to(z3, buff=0.26).set_y(brk.get_y())
            self.play(ReplacementTransform(brk, brk2), VGroup(z5_1, z6_2).animate.shift(0.14*RIGHT))
            self.wait()
            self.play(Restore(asso_a))
            dist_am.save_state()
            self.play(dist_am.animate.scale(scl).set_color(YELL_G).set_stroke(color=average_color(YELL_G[0], YELL_G[-1])))
            z8_1 = TexGen(r'(0+0)', isMath=True, font_sz=50).next_to(z3, buff=bff).set_y(brk2.get_y()).shift(0.02*DOWN)
            z8_2 = TexGen(r'\phantom{0} \cdot 0^{-1}', isMath=True, font_sz=50).next_to(z8_1, buff=0.15).shift(0.09*UP)
            z8 = VGroup(z8_1, z8_2)
            self.wait()
            self.play(ReplacementTransform(VGroup(brk2, z5_1, z6_1), z8), z6_2.animate.next_to(z8, buff=0.15, aligned_edge=DOWN))
            self.wait()
            self.play(Restore(dist_am))
            ident_a.save_state()
            self.play(ident_a.animate.scale(scl).set_color(YELL_G).set_stroke(color=average_color(YELL_G[0], YELL_G[-1])))
            self.wait()
            z9 = TexGen(r'0', isMath=True, font_sz=50).next_to(z3, buff=bff, aligned_edge=DOWN).shift(0.01*DOWN)
            self.play(ReplacementTransform(z8_1, z9), VGroup(z8_2, z6_2).animate.shift(1.22*LEFT))
            self.wait()
            self.play(Restore(ident_a))
            invs_a.save_state()
            self.play(invs_a.animate.scale(scl).set_color(YELL_G).set_stroke(color=average_color(YELL_G[0], YELL_G[-1])))
            self.wait()
            z10 = deepcopy(z9)
            self.play(ReplacementTransform(VGroup(z9, z8_2, z6_2), z10))
            self.wait()
            self.play(Restore(invs_a))
            self.play(VGroup(z2, z3, z10).animate.move_to(ORIGIN).shift(2.5*DOWN).set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1])))
            self.wait()
            aneq02 = TexGen(r'a \neq 0', isMath=True, font_sz=40, col=RED_G).next_to(invs_m, buff=0.5).shift(0.07*DOWN)
            self.play(ReplacementTransform(VGroup(z2, z3, z10), aneq02))
            self.wait()
            self.play(FadeOut(asso, asso_a, asso_m, commu, commu_a, commu_m, ident, ident_a, ident_m, invs, invs_a, invs_m, dist, dist_am, plus, cdot))
            ding_c1 = Tex(r'\ding{108}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2)
            ding_c2 = deepcopy(ding_c1).next_to(ding_c1, buff=0.1)
            ding_c3 = deepcopy(ding_c1).next_to(ding_c2, buff=0.1)
            ding_c4 = deepcopy(ding_c1).next_to(ding_c3, buff=0.1)
            ding_c5 = deepcopy(ding_c1).next_to(ding_c4, buff=0.1)
            dingcs = VGroup(ding_c1, ding_c2, ding_c3, ding_c4, ding_c5)
            dingcs.move_to([-3, 1, 0])
            self.play(ReplacementTransform(ding1, ding_c1), ReplacementTransform(ding2, ding_c2), ReplacementTransform(ding3, ding_c3), ReplacementTransform(ding4, ding_c4), ReplacementTransform(ding5, ding_c5),
                      aneq02.animate.next_to(ding_c4, DOWN))
            
        def play_you():
            ding_c1 = Tex(r'\ding{108}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2)
            ding_c2 = deepcopy(ding_c1).next_to(ding_c1, buff=0.1)
            ding_c3 = deepcopy(ding_c1).next_to(ding_c2, buff=0.1)
            ding_c4 = deepcopy(ding_c1).next_to(ding_c3, buff=0.1)
            ding_c5 = deepcopy(ding_c1).next_to(ding_c4, buff=0.1)
            dingcs = VGroup(ding_c1, ding_c2, ding_c3, ding_c4, ding_c5)
            dingcs.move_to([-3, 1, 0])
            aneq02 = TexGen(r'a \neq 0', isMath=True, font_sz=40, col=RED_G).next_to(ding_c4, DOWN)
            self.add(dingcs, aneq02)
            world = ImageMobject('world.png')
            world.height = 3
            self.play(BounceIn(world.next_to(dingcs, DOWN, buff=1)))
            self.wait()
            ding_n1 = Tex(r'\ding{74}', tex_template=tex_marks, font_size=75).set_color(AXCOL).set_stroke(color=average_color(AXCOL[0], AXCOL[-1]), width=2)
            ding_n2 = deepcopy(ding_n1).next_to(ding_n1, buff=0.1)
            ding_n3 = deepcopy(ding_n1).next_to(ding_n2, buff=0.1)
            ding_n4 = deepcopy(ding_n1).next_to(ding_n3, buff=0.1)
            ding_n5 = deepcopy(ding_n1).next_to(ding_n4, buff=0.1)
            dings_n = VGroup(ding_n1, ding_n2, ding_n3, ding_n4, ding_n5).move_to([3, 1, 0])
            r_arr = TexGen(r'\rightarrow', isMath=True, font_sz=100).shift(1*UP)
            you = TexGen(r'YOU', isMath=False, font_sz=50).next_to(dings_n, UP)
            you2 = TexGen(r'\neq \textup{YOU}', isMath=True, font_sz=100, col=RED_G)
            aeq0 = TexGen(r'a = 0', isMath=True, font_sz=40, col=GREEN_G).next_to(ding_n4, DOWN)
            self.play(DrawTxt(you))
            self.play(BounceIn(dings_n), DrawTxt(r_arr), DrawTxt(aeq0))
            self.play(world.animate.next_to(dings_n, DOWN, buff=1))
            self.wait()
            self.play(FadeOut(dings_n, aneq02, r_arr, world, dingcs, aeq0))
            self.play(ReplacementTransform(you, you2))

        # ANIMATE
        self.wait()
        play_intro()
        play_math()
        play_zero()
        play_you()
        # Thumbnail:
        z = TexGen(r'\frac{0}{0}', isMath=True, font_sz=210)
        t = TexGen(r'YES,', isMath=False, font_sz=210)
        j = TexGen(r'BUT $\ldots$', isMath=False, font_sz=210, col=YEBLUE_G).next_to(t, DOWN, buff=1, aligned_edge=LEFT)
        VGroup(z, VGroup(t,j).next_to(z, buff=1.5)).move_to(ORIGIN)
        self.add(z, t, j)
        self.wait()
