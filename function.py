import numpy as np
from manim import *
from manim.opengl import *
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

class Scenery(ThreeDScene):
    def construct(self):
        # COLORS
        WHITE_G = color_gradient([WHITE, WHITE], 2)
        BLACK_G = color_gradient([BLACK, BLACK], 2)
        YEBLUE_G = color_gradient([ManimColor.from_hex("#FFED95"), ManimColor.from_hex("#16E3F9")], 200)
        YELL_G = color_gradient([ManimColor.from_hex("#FEFE99"), ManimColor.from_hex("#FFC655")], 200)
        GREEN_G = color_gradient([ManimColor.from_hex("#BFFF97"), ManimColor.from_hex("#00C849")], 200)
        RED_G = color_gradient([ManimColor.from_hex("#FF7490"), ManimColor.from_hex("#FF0033")], 200)
        BGRAY_G = color_gradient([ManimColor.from_hex("#7E7E7E"), ManimColor.from_hex("#B1B1B1")], 200)
        BGRAY_G = color_gradient([ManimColor.from_hex("#5F5F5F"), ManimColor.from_hex("#949494")], 200)
        GRAY_G = color_gradient([ManimColor.from_hex("#212121"), ManimColor.from_hex("#505050")], 200)
        XY_G = color_gradient([ManimColor.from_hex("#FF68FC"), ManimColor.from_hex("#16E3F9")], 200)
        XY_G_R = color_gradient([ManimColor.from_hex("#16E3F9"), ManimColor.from_hex("#FF68FC")], 200)
        X_G = color_gradient([average_color(XY_G[0], XY_G[-1]), XY_G[-1], XY_G[-1]], 200)
        Y_G = color_gradient([XY_G[0], XY_G[0], average_color(XY_G[0], XY_G[-1])], 200)

        # TEX TEMPLATE
        snsus_tex = TexTemplate(tex_compiler='lualatex')
        snsus_tex.add_to_preamble(r'\usepackage{pifont}')
        
        # SPECIFIC FUNCTIONS
        def TexGen(string, font_sz=50, col=WHITE_G, isMath=False, stroke_w=1.0, avgStrokeCol=True):
            if not isMath:
                if avgStrokeCol:
                    return Tex(fr'{string}', font_size=font_sz, tex_template=snsus_tex).set_color(col).set_stroke(color=average_color(col[0], col[-1]), width=stroke_w)
                else: return Tex(fr'{string}', font_size=font_sz, tex_template=snsus_tex).set_color(col).set_stroke(color=col, width=stroke_w)
            else:
                if avgStrokeCol:
                    return MathTex(fr'{string}', font_size=font_sz, tex_template=snsus_tex).set_color(col).set_stroke(color=average_color(col[0], col[-1]), width=stroke_w)
                else: return MathTex(fr'{string}', font_size=font_sz, tex_template=snsus_tex).set_color(col).set_stroke(color=col, width=stroke_w)
                
        def DrawTxt(txt, stroke_w=2.0):
            return DrawBorderThenFill(txt, stroke_color=txt.get_stroke_colors(), stroke_width=stroke_w, run_time=1)
        
        def BounceIn(mobjects, run_t=0.5) -> Animation:
            bounce_anims = []
            for mob in mobjects:
                bounce_anims.append(GrowFromCenter(mob, rate_func=rate_functions.ease_out_back, run_time=run_t))
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
        
        def PersonGen(txt):
            return VGroup(SVGMobject("person.svg", height=1, stroke_width=0), Circle(0.08, BLACK).set_stroke(color=BLACK).set_fill(color=BLACK, opacity=1).shift(0.24*UP+0.12*LEFT),
                          Circle(0.08, BLACK).set_stroke(color=BLACK).set_fill(color=BLACK, opacity=1).shift(0.24*UP+0.12*RIGHT), TexGen(rf'{txt}', col=BLACK_G, font_sz=31, stroke_w=1.8).shift(0.29*DOWN))
        
        def SetGen(elements, tup=False, col=WHITE_G):
            if tup:
                open_bracket = TexGen(r'(', col=col).scale_to_fit_height(elements[0].height*(1.2))
                closing_bracket = TexGen(r')', col=col).scale_to_fit_height(elements[0].height*(1.2))
            else:
                open_bracket = TexGen(r'\{', col=col).scale_to_fit_height(elements[0].height*(1.2))
                closing_bracket = TexGen(r'\}', col=col).scale_to_fit_height(elements[0].height*(1.2))
            set_to_return = VGroup(open_bracket, elements[0].next_to(open_bracket, buff=0))
            comma = TexGen(r',', col=col).scale_to_fit_height(open_bracket.height/4)
            set_to_return.add(comma.next_to(set_to_return[-1], aligned_edge=DOWN, buff=0.1).shift(comma.height/3*DOWN))
            prev_comma = comma
            prev_e = elements[0]
            for e in elements[1:]:
                set_to_return.add(e.next_to(prev_e, buff=comma.height*1.5, aligned_edge=DOWN))
                if e != elements[-1]:
                    cur_comma = deepcopy(comma).next_to(e, aligned_edge=DOWN, buff=0.1).shift(comma.height/3*DOWN)
                    set_to_return.add(cur_comma)
                    prev_comma = cur_comma
                prev_e = e
            set_to_return.add(closing_bracket.next_to(elements[-1], buff=0))
            return set_to_return
        
        def ColorizeTup(tups, col=XY_G, X_col=X_G, Y_col=Y_G, scale=1.1) -> Animation:
            anims = []
            for tup in tups:
                anims.append(tup[0].animate.scale(scale).set_color(col).set_stroke(average_color(col[0], col[-1])))
                anims.append(tup[1][0].animate.scale(scale).set_color(X_col).set_stroke(X_col))
                anims.append(tup[2].animate.scale(scale).set_color(col).set_stroke(average_color(col[0], col[-1])))
                anims.append(tup[3][0].animate.scale(scale).set_color(Y_col).set_stroke(Y_col))
                anims.append(tup[4].animate.scale(scale).set_color(col).set_stroke(average_color(col[0], col[-1])))
            return anims
        
        def play_intro():
            f = TexGen(r'f', isMath=True, font_sz=100).next_to(machine, UP)
            machine_t = TexGen(r'``MACHINE"', font_sz=85, col=BLACK_G).move_to(machine).set_z_index(1)
            in_x = TexGen(r'x', isMath=True, font_sz=100).next_to(machine, LEFT, buff=1.5)
            out_y = TexGen(r'y', isMath=True, font_sz=100).move_to(machine)
            self.play(DrawTxt(f))
            self.wait()
            self.play(FadeIn(machine, run_time=0.7))
            self.play(DrawTxt(machine_t))
            self.wait()
            self.play(GrowFromCenter(left_stripe, rate_func=linear, run_time=0.6))
            self.play(DrawTxt(in_x))
            self.play(in_x.animate.move_to(machine_t))
            self.remove(in_x)
            self.play(GrowFromCenter(right_stripe, rate_func=linear, run_time=0.6))
            self.play(out_y.animate.next_to(machine, buff=1.5))
            self.play(FadeOut(out_y))
            self.wait()
            bugfree = TexGen(r'bug-free', font_sz=100, col=GREEN_G).next_to(machine, DOWN, buff=0.5)
            self.play(DrawTxt(bugfree))
            self.wait()
            calc = TexGen(r'``calculates"', font_sz=100, col=GREEN_G).next_to(machine, DOWN, buff=0.5)
            self.play(ReplacementTransform(bugfree, calc))
            self.wait()
            self.play(machine_t.animate.become(TexGen(r'y = 2 \cdot x', isMath=True, font_sz=100, col=BLACK_G).move_to(machine)))
            in_3 = TexGen(r'3', isMath=True, font_sz=100).next_to(machine, LEFT, buff=1.5)
            self.play(DrawTxt(in_3), run_time=0.6)
            self.play(in_3.animate.move_to(machine_t).set_z_index(-1), run_time=0.6)
            self.remove(in_3)
            out_6 = TexGen(r'6', isMath=True, font_sz=100).move_to(machine)
            self.play(out_6.animate.next_to(machine, buff=1.5), run_time=0.6)
            self.play(FadeOut(out_6), run_time=0.6)
            self.play(machine_t.animate.become(TexGen(r'?', isMath=False, font_sz=100, col=BLACK_G).move_to(machine)), calc.animate.set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1])))
            in_3 = TexGen(r'3', isMath=True, font_sz=100).next_to(machine, LEFT, buff=1.5)
            self.play(DrawTxt(in_3), run_time=0.6)
            self.play(in_3.animate.move_to(machine_t).set_z_index(-1), run_time=0.6)
            self.remove(in_3)
            out_4 = TexGen(r'4', isMath=True, font_sz=100).move_to(machine)
            self.play(out_4.animate.next_to(machine, buff=1.5), run_time=0.6)
            in_67 = TexGen(r'67', isMath=True, font_sz=100).next_to(machine, LEFT, buff=1.5)
            self.play(DrawTxt(in_67), FadeOut(out_4), run_time=0.6)
            self.play(in_67.animate.move_to(machine_t).set_z_index(-1), run_time=0.6)
            self.remove(in_67)
            out_42 = TexGen(r'42', isMath=True, font_sz=100).move_to(machine)
            self.play(out_42.animate.next_to(machine, buff=1.5), run_time=0.6)
            self.play(FadeOut(out_42), run_time=0.6)
            self.wait()
            self.play(machine_t.animate.set_color(WHITE_G).set_stroke(color=WHITE_G), machine.animate.fade(darkness=1), left_stripe.animate.fade(darkness=0), 
                      right_stripe.animate.fade(darkness=0), FadeOut(calc), f.animate.shift(0.6*DOWN))
            self.wait()
            self.play(machine_t.animate.become(TexGen(r'IS', isMath=False, font_sz=100, col=WHITE_G).move_to(machine)))
            ltotrun = TexGen(r'binary, left-total, right-unique', isMath=False, font_sz=80, col=WHITE_G).next_to(machine_t, 3*DOWN)
            relation = TexGen(r'Relation', isMath=False, font_sz=80, col=WHITE_G).next_to(ltotrun, DOWN)
            self.wait()
            self.play(DrawTxt(ltotrun), DrawTxt(relation))
            self.wait()
            self.play(FadeOut(f, ltotrun)) 
            self.play(relation.animate.next_to(machine_t, 3*UP), run_time=0.8)
            set_t = TexGen(r'Set', isMath=False, font_sz=80, col=WHITE_G)
            of_t = TexGen(r'of', isMath=False, font_sz=80, col=WHITE_G).next_to(set_t, buff=0.3, aligned_edge=DOWN)
            tup_t = TexGen(r'Tuples', isMath=False, font_sz=80, col=WHITE_G).next_to(of_t, buff=0.3, aligned_edge=UP)
            set_of_tupls = VGroup(set_t, of_t, tup_t).move_to(ltotrun)
            self.wait()
            self.play(DrawTxt(set_of_tupls))
            self.wait()
            set_1 = TexGen(r'\{a, b, c\}', isMath=True, font_sz=50, col=WHITE_G).next_to(set_t, 1.5*DOWN)
            set_2 = TexGen(r'\{1, 2, 3\}', isMath=True, font_sz=50, col=WHITE_G).next_to(set_t, 1.5*DOWN)
            self.play(DrawTxt(set_1))
            self.wait()
            self.play(ReplacementTransform(set_1, set_2))
            tup_1 = TexGen(r'(a, b, c)', isMath=True, font_sz=50, col=WHITE_G).next_to(tup_t, 1.5*DOWN).set_y(set_1.get_y())
            tup_neq = TexGen(r'\neq', isMath=True, font_sz=50, col=RED_G).next_to(tup_1, DOWN, buff=0.09)
            tup_2 = TexGen(r'(1, 2, 3)', isMath=True, font_sz=50, col=WHITE_G).move_to(tup_1)
            tup_3 = TexGen(r'(1, 3, 2)', isMath=True, font_sz=50, col=WHITE_G).next_to(tup_neq, DOWN, buff=0.09)
            set_eq = TexGen(r'=', isMath=True, font_sz=50, col=GREEN_G).next_to(set_1, DOWN, buff=0.1).set_y(tup_neq.get_y())
            set_3 = TexGen(r'\{1, 3, 2\}', isMath=True, font_sz=50, col=WHITE_G).next_to(set_eq, DOWN).set_y(tup_3.get_y())
            self.wait()
            self.play(DrawTxt(tup_1))
            self.wait()
            self.play(ReplacementTransform(tup_1, tup_2))
            self.wait()
            self.play(DrawTxt(set_3))
            self.play(DrawTxt(set_eq))
            self.wait()
            self.play(DrawTxt(tup_3))
            self.play(DrawTxt(tup_neq))
            self.wait()
            self.play(FadeOut(set_2, set_3, set_eq, tup_3, tup_neq))
            self.wait()
            three_tup = TexGen(r'3-Tuple', isMath=False, font_sz=50, col=WHITE_G).next_to(tup_1, DOWN)
            four_tup = TexGen(r'4-Tuple', isMath=False, font_sz=50, col=WHITE_G).move_to(three_tup)
            two_tup = TexGen(r'2-Tuple', isMath=False, font_sz=50, col=WHITE_G).move_to(three_tup)
            triple = TexGen(r'Triple', isMath=False, font_sz=50, col=WHITE_G).move_to(three_tup)
            pair = TexGen(r'Pair', isMath=False, font_sz=50, col=WHITE_G).move_to(three_tup)
            tup_4 = TexGen(r'(1, 2, 3, 4)', isMath=True, font_sz=50, col=WHITE_G).move_to(tup_2)
            tup_pair = TexGen(r'(1, 2)', isMath=True, font_sz=50, col=WHITE_G).move_to(tup_2)
            self.play(DrawTxt(three_tup))
            self.wait()
            three_tup_cp = deepcopy(three_tup)
            tup_2_cp = deepcopy(tup_2)
            self.play(ReplacementTransform(three_tup, four_tup), ReplacementTransform(tup_2, tup_4))
            self.wait()
            self.play(ReplacementTransform(four_tup, three_tup_cp), ReplacementTransform(tup_4, tup_2_cp))
            self.wait()
            self.play(ReplacementTransform(three_tup_cp, triple))
            self.wait()
            self.play(ReplacementTransform(triple, two_tup), ReplacementTransform(tup_2_cp, tup_pair))
            self.wait()
            self.play(ReplacementTransform(two_tup, pair))
            self.wait()
            self.play(FadeOut(pair, tup_pair))
            self.wait()
            binary = TexGen(r'binary', isMath=False, font_sz=80, col=WHITE_G).next_to(relation, UP)
            pairs = TexGen(r'Pairs', isMath=False, font_sz=80, col=WHITE_G).next_to(of_t, buff=0.3, aligned_edge=UP)
            pair_x = VGroup(deepcopy(set_t), deepcopy(of_t), deepcopy(pairs)).get_x()
            self.play(DrawTxt(binary))
            self.play(ReplacementTransform(tup_t, pairs))
            self.play(VGroup(set_t, of_t, pairs).animate.shift(-pair_x*RIGHT))
            self.wait()
            R_sub = TexGen(r'R \subseteq', isMath=True, font_sz=80)
            X = TexGen(r'X', isMath=True, font_sz=80).next_to(R_sub, aligned_edge=UP, buff=0.33)
            times = TexGen(r'\times', isMath=True, font_sz=80).next_to(X, aligned_edge=DOWN)
            Y = TexGen(r'Y', isMath=True, font_sz=80).next_to(times, aligned_edge=DOWN)
            subset = VGroup(R_sub, X, times, Y).next_to(VGroup(set_t, of_t, pairs), 2*DOWN)
            self.play(DrawTxt(subset))
            self.wait()
            self.play(FadeOut(relation, machine_t, binary, set_t, of_t, pairs, R_sub, times)) 
            self.play(X.animate.move_to([-3.5, 3, 0]), Y.animate.move_to([3.5, 3, 0]))

        def play_relation():
            X = TexGen(r'X', isMath=True, font_sz=80).move_to([-3.5, 3, 0])
            Y = TexGen(r'Y', isMath=True, font_sz=80).move_to([3.5, 3, 0])
            self.add(X, Y)
            self.wait()
            you = PersonGen('YOU').scale_to_fit_height(0.7)
            mom = PersonGen('MOM').scale_to_fit_height(0.7)
            dad = PersonGen('DAD').scale_to_fit_height(0.7)
            set_X = SetGen([you, mom, dad]).next_to(X, DOWN)
            set_Y = deepcopy(set_X).next_to(Y, DOWN)
            self.play(DrawTxt(set_X[0]), BounceIn(set_X[1]),
                      DrawTxt(set_X[2]), BounceIn(set_X[3]),
                      DrawTxt(set_X[4]), BounceIn(set_X[5]), DrawTxt(set_X[6]))
            self.wait()
            self.play(DrawTxt(set_Y[0]), BounceIn(set_Y[1]),
                      DrawTxt(set_Y[2]), BounceIn(set_Y[3]),
                      DrawTxt(set_Y[4]), BounceIn(set_Y[5]), DrawTxt(set_Y[6]))
            self.wait()
            times = TexGen(r'\times', isMath=True, font_sz=80).next_to(X, aligned_edge=DOWN).set_x(0)
            self.play(DrawTxt(times))
            self.wait()
            Y_start = np.array([-6, -1.1, 0])
            Y_buff = np.array([0, 1.7, 0])
            X_buff = np.array([1.7, 0, 0])
            X_start = np.array(Y_start-Y_buff+X_buff)
            x = TexGen(r'x', isMath=True, font_sz=80).move_to(X, aligned_edge=DOWN)
            y = TexGen(r'y', isMath=True, font_sz=80).move_to(Y, aligned_edge=DOWN)
            self.play(FadeOut(set_X[0], set_X[2], set_X[4], set_X[6]), ReplacementTransform(X, x))
            self.play(set_X[1].animate.move_to(X_start), set_X[3].animate.move_to(X_start+X_buff), set_X[5].animate.move_to(X_start+2*X_buff), x.animate.move_to(X_start+2*X_buff).shift([1, -0.6, 0]))
            self.play(times.animate.move_to(Y_start-Y_buff))
            self.play(FadeOut(set_Y[0], set_Y[2], set_Y[4], set_Y[6]), ReplacementTransform(Y, y))
            self.play(set_Y[1].animate.move_to(Y_start), set_Y[3].animate.move_to(Y_start+Y_buff), set_Y[5].animate.move_to(Y_start+2*Y_buff), y.animate.move_to(Y_start+2*Y_buff).shift([-0.6, 1, 0]))
            tup_scale = 0.6
            tup_YY = SetGen([deepcopy(you), deepcopy(you)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+X_buff)
            tup_MY = SetGen([deepcopy(mom), deepcopy(you)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+2*X_buff)
            tup_DY = SetGen([deepcopy(dad), deepcopy(you)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+3*X_buff)
            tup_YM = SetGen([deepcopy(you), deepcopy(mom)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+X_buff+Y_buff)
            tup_MM = SetGen([deepcopy(mom), deepcopy(mom)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+2*X_buff+Y_buff)
            tup_DM = SetGen([deepcopy(dad), deepcopy(mom)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+3*X_buff+Y_buff)
            tup_YD = SetGen([deepcopy(you), deepcopy(dad)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+X_buff+2*Y_buff)
            tup_MD = SetGen([deepcopy(mom), deepcopy(dad)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+2*X_buff+2*Y_buff)
            tup_DD = SetGen([deepcopy(dad), deepcopy(dad)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+3*X_buff+2*Y_buff)
            all_tups = VGroup(tup_YY, tup_MY, tup_DY, tup_YM, tup_MM, tup_DM, tup_YD, tup_MD, tup_DD)
            for tup in all_tups:
                tup[1][0].set_color(BGRAY_G)
                tup[3][0].set_color(BGRAY_G)
                tup.save_state()
            self.wait()
            self.play(set_X[1][0].animate.set_color(X_G))
            self.play(set_Y[1][0].animate.set_color(Y_G))
            tup_YY[0].set_color(XY_G).set_stroke(average_color(XY_G[0], XY_G[-1]))
            tup_YY[1][0].set_color(X_G).set_stroke(X_G)
            tup_YY[2].set_color(XY_G).set_stroke(average_color(XY_G[0], XY_G[-1]))
            tup_YY[3][0].set_color(Y_G).set_stroke(Y_G)
            tup_YY[4].set_color(XY_G).set_stroke(average_color(XY_G[0], XY_G[-1]))
            self.play(FadeIn(tup_YY[1], target_position=set_X[1]), FadeIn(tup_YY[3], target_position=set_Y[1]))
            self.play(DrawTxt(tup_YY[0]), DrawTxt(tup_YY[2]), DrawTxt(tup_YY[4]))
            self.wait()
            self.play(tup_YY[1][0].animate.set_color(BGRAY_G), tup_YY[3][0].animate.set_color(BGRAY_G), set_X[1][0].animate.set_color(WHITE_G), set_Y[1][0].animate.set_color(WHITE_G), 
                      tup_YY[0].animate.set_color(BGRAY_G).set_stroke(BGRAY_G), tup_YY[2].animate.set_color(BGRAY_G).set_stroke(BGRAY_G), tup_YY[4].animate.set_color(BGRAY_G).set_stroke(BGRAY_G))
            self.play(FadeIn(tup_MY[1], target_position=set_X[3]), FadeIn(tup_MY[3], target_position=set_Y[1]),
                      FadeIn(tup_DY[1], target_position=set_X[5]), FadeIn(tup_DY[3], target_position=set_Y[1]),
                      FadeIn(tup_YM[1], target_position=set_X[1]), FadeIn(tup_YM[3], target_position=set_Y[3]),
                      FadeIn(tup_MM[1], target_position=set_X[3]), FadeIn(tup_MM[3], target_position=set_Y[3]),
                      FadeIn(tup_DM[1], target_position=set_X[5]), FadeIn(tup_DM[3], target_position=set_Y[3]),
                      FadeIn(tup_YD[1], target_position=set_X[1]), FadeIn(tup_YD[3], target_position=set_Y[5]),
                      FadeIn(tup_MD[1], target_position=set_X[3]), FadeIn(tup_MD[3], target_position=set_Y[5]),
                      FadeIn(tup_DD[1], target_position=set_X[5]), FadeIn(tup_DD[3], target_position=set_Y[5]))
            self.play(DrawTxt(tup_MY[0]), DrawTxt(tup_MY[2]), DrawTxt(tup_MY[4]),
                      DrawTxt(tup_DY[0]), DrawTxt(tup_DY[2]), DrawTxt(tup_DY[4]),
                      DrawTxt(tup_YM[0]), DrawTxt(tup_YM[2]), DrawTxt(tup_YM[4]),
                      DrawTxt(tup_MM[0]), DrawTxt(tup_MM[2]), DrawTxt(tup_MM[4]),
                      DrawTxt(tup_DM[0]), DrawTxt(tup_DM[2]), DrawTxt(tup_DM[4]),
                      DrawTxt(tup_YD[0]), DrawTxt(tup_YD[2]), DrawTxt(tup_YD[4]),
                      DrawTxt(tup_MD[0]), DrawTxt(tup_MD[2]), DrawTxt(tup_MD[4]),
                      DrawTxt(tup_DD[0]), DrawTxt(tup_DD[2]), DrawTxt(tup_DD[4]))
            self.wait()
            XtimesY = TexGen(r'X \times Y', isMath=True, col=XY_G, font_sz=100).move_to([3.5, tup_MM.get_y(), 0])
            sub = TexGen(r'\subseteq', isMath=True, col=BGRAY_G, font_sz=100).next_to(XtimesY, UP, buff=0.5)
            eq = TexGen(r'=', isMath=True, font_sz=100).move_to(sub)
            R = TexGen(r'R', isMath=True, font_sz=100).next_to(sub, UP, buff=0.5)
            empty = TexGen(r'\{\}', isMath=True, col=XY_G, font_sz=100).move_to(R)
            R_set = TexGen(r'\{\phantom{(x, y|)} | \phantom{x\textup{ ``loves" }y|}\}', isMath=True, font_sz=55).move_to(XtimesY)
            xy_obracket = TexGen(r'(', isMath=True, font_sz=55)
            xy_x = TexGen(r'x', isMath=True, font_sz=55).next_to(xy_obracket, buff=0.06)
            xy_comma = TexGen(r',', isMath=True, font_sz=55).next_to(xy_x, buff=0.06).shift(0.16*DOWN)
            xy_y = TexGen(r'y', isMath=True, font_sz=55).next_to(xy_x, aligned_edge=UP, buff=0.33)
            xy_cbracket = TexGen(r')', isMath=True, font_sz=55).next_to(xy_y, buff=0.06).set_y(xy_obracket.get_y())
            xy = VGroup(xy_obracket, xy_x, xy_comma, xy_y, xy_cbracket).move_to(R_set).set_x(1.95)
            cond = TexGen(r'Condition', isMath=False, font_sz=55).move_to(R_set).set_x(4.34)
            cond_love = TexGen(r'$x$ ``loves" $y$', isMath=False, font_sz=55).move_to(cond)
            self.play(ColorizeTup(all_tups))
            self.play(DrawTxt(XtimesY))
            self.wait()
            self.play(*(Restore(tup) for tup in all_tups), XtimesY.animate.set_color(BGRAY_G).set_stroke(BGRAY_G))
            self.play(DrawTxt(sub), DrawTxt(R))
            self.wait()
            self.play(ColorizeTup([tup_YD, tup_MY, tup_MM, tup_DM]), R.animate.set_color(XY_G).set_stroke(average_color(XY_G[0], XY_G[-1])))
            self.wait()
            self.play(ColorizeTup([tup_YY, tup_YM, tup_MD, tup_DD, tup_DY]))
            self.wait()
            self.play(*(Restore(tup) for tup in all_tups))
            self.wait()
            R_cp = deepcopy(R)
            empty_cp = deepcopy(empty)
            self.play(ReplacementTransform(R, empty))
            self.wait()
            self.play(ReplacementTransform(empty, R_cp))
            self.wait()
            self.play(ReplacementTransform(sub, eq), ReplacementTransform(XtimesY, VGroup(R_set, xy)))
            self.wait()
            self.play(DrawTxt(cond))
            self.wait()
            self.play(ReplacementTransform(cond, cond_love))
            self.wait()
            self.play(set_X[3][0].animate.set_color(X_G).set_stroke(X_G))
            self.play(set_Y[1][0].animate.set_color(Y_G).set_stroke(Y_G))
            self.play(ColorizeTup([tup_MY]))
            self.wait()
            self.play(set_X[3][0].animate.set_color(WHITE_G).set_stroke(WHITE_G), set_Y[1][0].animate.set_color(WHITE_G).set_stroke(WHITE_G))
            self.play(ColorizeTup([tup_DY, tup_YM, tup_DM, tup_YD, tup_MD]))
            self.wait()
            self.play(ColorizeTup([tup_YY, tup_MM, tup_DD]))
            self.wait()
            self.play(*(Restore(tup) for tup in all_tups), ReplacementTransform(R_cp, empty_cp))

        def play_love():
            you = PersonGen('YOU').scale_to_fit_height(0.7)
            mom = PersonGen('MOM').scale_to_fit_height(0.7)
            dad = PersonGen('DAD').scale_to_fit_height(0.7)
            set_X = SetGen([you, mom, dad])
            set_Y = deepcopy(set_X)
            Y_start = np.array([-6, -1.1, 0])
            Y_buff = np.array([0, 1.7, 0])
            X_buff = np.array([1.7, 0, 0])
            X_start = np.array(Y_start-Y_buff+X_buff)
            times = TexGen(r'\times', isMath=True, font_sz=80).move_to(Y_start-Y_buff)
            x = TexGen(r'x', isMath=True, font_sz=80).move_to(X_start+2*X_buff).shift([1, -0.6, 0])
            y = TexGen(r'y', isMath=True, font_sz=80).move_to(Y_start+2*Y_buff).shift([-0.6, 1, 0])
            set_X[1].move_to(X_start)
            set_X[3].move_to(X_start+X_buff)
            set_X[5].move_to(X_start+2*X_buff)
            set_Y[1].move_to(Y_start)
            set_Y[3].move_to(Y_start+Y_buff)
            set_Y[5].move_to(Y_start+2*Y_buff)
            tup_scale = 0.6
            tup_YY = SetGen([deepcopy(you), deepcopy(you)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+X_buff)
            tup_MY = SetGen([deepcopy(mom), deepcopy(you)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+2*X_buff)
            tup_DY = SetGen([deepcopy(dad), deepcopy(you)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+3*X_buff)
            tup_YM = SetGen([deepcopy(you), deepcopy(mom)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+X_buff+Y_buff)
            tup_MM = SetGen([deepcopy(mom), deepcopy(mom)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+2*X_buff+Y_buff)
            tup_DM = SetGen([deepcopy(dad), deepcopy(mom)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+3*X_buff+Y_buff)
            tup_YD = SetGen([deepcopy(you), deepcopy(dad)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+X_buff+2*Y_buff)
            tup_MD = SetGen([deepcopy(mom), deepcopy(dad)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+2*X_buff+2*Y_buff)
            tup_DD = SetGen([deepcopy(dad), deepcopy(dad)], tup=True, col=BGRAY_G).scale_to_fit_height(tup_scale).move_to(Y_start+3*X_buff+2*Y_buff)
            all_tups = VGroup(tup_YY, tup_MY, tup_DY, tup_YM, tup_MM, tup_DM, tup_YD, tup_MD, tup_DD)
            for tup in all_tups:
                tup[1][0].set_color(BGRAY_G)
                tup[3][0].set_color(BGRAY_G)
                tup.save_state()
            XtimesY = TexGen(r'X \times Y', isMath=True, col=XY_G, font_sz=100).move_to([3.5, tup_MM.get_y(), 0])
            sub = TexGen(r'\subseteq', isMath=True, col=BGRAY_G, font_sz=100).next_to(XtimesY, UP, buff=0.5)
            eq = TexGen(r'=', isMath=True, font_sz=100).move_to(sub)
            R = TexGen(r'R', isMath=True, col=XY_G, font_sz=100).next_to(sub, UP, buff=0.5)
            empty = TexGen(r'\{\}', isMath=True, col=XY_G, font_sz=100).move_to(R)
            R_set = TexGen(r'\{\phantom{(x, y|)} | \phantom{x\textup{ ``loves" }y|}\}', isMath=True, font_sz=55).move_to(XtimesY)
            xy_obracket = TexGen(r'(', isMath=True, font_sz=55)
            xy_x = TexGen(r'x', isMath=True, font_sz=55).next_to(xy_obracket, buff=0.06)
            xy_comma = TexGen(r',', isMath=True, font_sz=55).next_to(xy_x, buff=0.06).shift(0.16*DOWN)
            xy_y = TexGen(r'y', isMath=True, font_sz=55).next_to(xy_x, aligned_edge=UP, buff=0.33)
            xy_cbracket = TexGen(r')', isMath=True, font_sz=55).next_to(xy_y, buff=0.06).set_y(xy_obracket.get_y())
            xy = VGroup(xy_obracket, xy_x, xy_comma, xy_y, xy_cbracket).move_to(R_set).set_x(1.95)
            cond = TexGen(r'Condition', isMath=False, font_sz=55).move_to(R_set).set_x(4.34)
            cond_love = TexGen(r'$x$ ``loves" $y$', isMath=False, font_sz=55).move_to(cond)
            self.add(times, set_X[1], set_X[3], set_X[5], set_Y[1], set_Y[3], set_Y[5], *all_tups, eq, empty, R_set, xy, cond_love, x, y)
            self.play(ReplacementTransform(empty, R), ColorizeTup([tup_DY, tup_YM, tup_DM, tup_YD, tup_MD, tup_MY]))
            self.wait()
            u_arr = TexGen(r'\uparrow', isMath=True, font_sz=50).next_to(xy[1], DOWN)
            every_x = TexGen(r'every $x \in X$ ``loves"\\\underline{at least} one $y \in Y$', isMath=False, font_sz=55).next_to(R_set, 2.8*DOWN)
            every_x2 = TexGen(r'every $x \in X$ ``loves"\\\underline{at most} one $y \in Y$', isMath=False, font_sz=55).next_to(R_set, 2.8*DOWN)
            lefttotal = TexGen(r'left-\\total', isMath=False, font_sz=55).next_to(every_x, 1.5*DOWN)
            rightuni = TexGen(r'right-\\unique', isMath=False, font_sz=55).next_to(every_x2, 1.5*DOWN)
            r_arr = TexGen(r'\Rightarrow', isMath=True, font_sz=55).next_to(lefttotal, LEFT)
            self.play(xy_x.animate.set_color(X_G).set_stroke(average_color(X_G[0], X_G[-1])), DrawTxt(u_arr))
            self.play(DrawTxt(every_x))
            self.wait()
            self.play(DrawTxt(r_arr), DrawTxt(lefttotal))
            self.wait()
            self.play(lefttotal.animate.set_stroke(color=average_color(X_G[0], X_G[-1])).set_color(X_G))
            self.play(set_X[1][0].animate.set_color(X_G), set_X[3][0].animate.set_color(X_G), set_X[5][0].animate.set_color(X_G))
            self.wait()
            self.play(Restore(tup_DY), Restore(tup_DM), set_X[5][0].animate.set_color(RED_G), lefttotal.animate.set_stroke(color=average_color(RED_G[0], RED_G[-1])).set_color(RED_G))
            self.wait()
            self.play(set_X[1][0].animate.set_color(WHITE_G), set_X[3][0].animate.set_color(WHITE_G), set_X[5][0].animate.set_color(WHITE_G),
                      ColorizeTup([tup_DY, tup_DM]), FadeOut(every_x, lefttotal, r_arr))
            self.wait()
            self.play(u_arr.animate.next_to(xy_y, DOWN).set_y(u_arr.get_y()), xy_y.animate.set_color(Y_G).set_stroke(average_color(Y_G[0], Y_G[-1])), xy_x.animate.set_color(WHITE_G).set_stroke(WHITE_G))
            self.play(DrawTxt(every_x2))
            self.wait()
            self.play(DrawTxt(r_arr.next_to(rightuni, LEFT)), DrawTxt(rightuni))
            self.wait()
            self.play(rightuni.animate.set_stroke(color=average_color(RED_G[0], RED_G[-1])).set_color(RED_G))
            self.play(ColorizeTup([tup_YM, tup_YD], col=RED_G, X_col=RED_G, Y_col=RED_G, scale=1))
            self.wait()
            self.play(Restore(tup_YD), Restore(tup_MD), Restore(tup_DY), ColorizeTup([tup_YM], scale=1), rightuni.animate.set_stroke(color=average_color(Y_G[0], Y_G[-1])).set_color(Y_G))
            self.wait()
            self.play(Restore(tup_DM))
            self.wait()
            self.play(FadeOut(every_x2, u_arr, r_arr), xy_y.animate.set_color(WHITE_G).set_stroke(WHITE_G))
            self.play(rightuni.animate.move_to(every_x2, aligned_edge=UP).shift(1.2*RIGHT+0.2*UP), FadeIn(lefttotal.move_to(every_x2, aligned_edge=UP).shift(1.2*LEFT+0.2*UP)))
            self.wait()
            self.play(ColorizeTup([tup_DM]), lefttotal.animate.set_stroke(color=average_color(X_G[0], X_G[-1])).set_color(X_G))
            self.wait()
            eq2 = deepcopy(eq).shift(3.8*DOWN)
            f = TexGen(r'f', isMath=True, col=XY_G, font_sz=100).next_to(eq2, DOWN, buff=0.5)
            self.play(DrawTxt(eq2), DrawTxt(f))
            self.wait()
            X = TexGen(r'X', isMath=True, font_sz=80).move_to([-3.5, 3, 0])
            Y = TexGen(r'Y', isMath=True, font_sz=80).move_to([3.5, 3, 0])
            self.play(FadeOut(R, eq, R_set, xy, cond_love, lefttotal, rightuni, eq2, f, times, *all_tups, set_X[1], set_X[3], set_X[5], set_Y[1], set_Y[3], set_Y[5]))
            self.play(ReplacementTransform(x, X), ReplacementTransform(y, Y))

        def play_func():
            X = TexGen(r'X', isMath=True, font_sz=80).move_to([-3.5, 3, 0])
            Y = TexGen(r'Y', isMath=True, font_sz=80).move_to([3.5, 3, 0])
            RpX = TexGen(r'\mathbb{R}_{\geq 0}', isMath=True, font_sz=80).next_to(X, 1.5*DOWN)
            RpY = TexGen(r'\mathbb{R}_{\geq 0}', isMath=True, font_sz=80).next_to(Y, 1.5*DOWN)
            self.add(X, Y)
            self.wait()
            self.play(DrawTxt(RpX), DrawTxt(RpY))
            times = TexGen(r'\times', isMath=True, font_sz=80).next_to(X, aligned_edge=DOWN).set_x(0)
            x = TexGen(r'x', isMath=True, font_sz=80).move_to([0.5, -3.4, 0])
            y = TexGen(r'y', isMath=True, font_sz=80).move_to([-6.5, 3.4, 0])
            x_line = NumberLine(x_range=[0, 6], length=6, include_ticks=False, exclude_origin_tick=True, include_tip=True, stroke_width=5, tip_shape=StealthTip, tip_height=0.2).move_to([-6, -3, 0], aligned_edge=LEFT)
            y_line = deepcopy(x_line).rotate(PI/2, about_point=[-6, -3, 0])
            self.wait()
            self.play(DrawTxt(times))
            self.wait()
            self.play(ReplacementTransform(X, x), ReplacementTransform(RpX, x_line))
            self.play(times.animate.move_to([-6, -3, 0]))
            self.play(ReplacementTransform(Y, y), ReplacementTransform(RpY, y_line))
            self.wait()
            XxY = Rectangle(color=XY_G_R, height=6, width=6).move_to(x_line, aligned_edge=DL).shift(0.1*UP).set_fill(color=XY_G_R, opacity=1).set_stroke(color=XY_G_R, width=0).set_z_index(-1)
            XtimesY = TexGen(r'X \times Y', isMath=True, col=XY_G, font_sz=100).move_to([3.5, 0, 0])
            sub = TexGen(r'\subseteq', isMath=True, col=BGRAY_G, font_sz=100).next_to(XtimesY, UP, buff=0.5)
            eq = TexGen(r'=', isMath=True, font_sz=100).move_to(sub)
            R = TexGen(r'R', isMath=True, col=XY_G, font_sz=100).next_to(sub, UP, buff=0.5)
            self.play(GrowFromPoint(XxY, point=times))
            self.wait()
            self.play(DrawTxt(XtimesY))
            self.wait()
            self.play(XxY.animate.set_color(GRAY_G).set_fill(GRAY_G), XtimesY.animate.set_stroke(color=average_color(BGRAY_G[0], BGRAY_G[-1])).set_color(BGRAY_G))
            self.play(DrawTxt(R), DrawTxt(sub))
            self.wait()
            lefttotal = TexGen(r'left-\\total', isMath=False, font_sz=55).next_to(XtimesY, 1.5*DOWN).shift(1.2*LEFT)
            rightuni = TexGen(r'right-\\unique', isMath=False, font_sz=55).next_to(lefttotal, aligned_edge=UP).set_x(lefttotal.get_x()+2.4)
            heart = SVGMobject("heart.svg", height=5).move_to(XxY).set_color(XY_G).set_fill(color=XY_G, opacity=1).shift(0.25*DOWN)
            logo = Tex(fr's', font_size=900).set_color(XY_G).set_stroke(color=XY_G, width=14, background=True).rotate(-PI, axis=UP).rotate(-PI/2).move_to(XxY)
            curve = SVGMobject("curve.svg", width=4).move_to(XxY).set_color(XY_G).set_fill(opacity=0).set_stroke(width=10)
            curve2 = SVGMobject("curve2.svg", width=6).stretch_to_fit_height(curve.height).move_to(XxY).set_color(XY_G).set_fill(opacity=0).set_stroke(width=10)
            self.play(FadeIn(heart))
            self.wait()
            self.play(ReplacementTransform(heart, logo))
            self.wait()
            self.play(ReplacementTransform(logo, curve, path_func=clockwise_path()))
            self.wait()
            vline = Line(start=[-0.6, -3, 0], end=[-0.6, 2.98, 0]).set_color(RED_G).set_stroke(RED_G)
            P1 = Circle(radius=0.1).move_to([-0.6-3.1, -0.8, 0]).set_fill(RED_G, opacity=1).set_stroke(color=RED_G)
            P2 = Circle(radius=0.1).move_to([-0.6-3.1, -0.16, 0]).set_fill(RED_G, opacity=1).set_stroke(color=RED_G)
            P3 = Circle(radius=0.1).move_to([-0.6-3.1, 0.61, 0]).set_fill(RED_G, opacity=1).set_stroke(color=RED_G)
            self.play(DrawTxt(lefttotal), DrawTxt(rightuni))
            self.wait()
            self.play(lefttotal.animate.set_stroke(color=average_color(RED_G[0], RED_G[-1])).set_color(RED_G))
            self.play(Create(vline))
            self.wait()
            self.play(curve.animate.stretch_to_fit_width(6), vline.animate.set_color(X_G), lefttotal.animate.set_stroke(color=average_color(X_G[0], X_G[-1])).set_color(X_G))
            self.wait()
            self.play(rightuni.animate.set_stroke(color=average_color(RED_G[0], RED_G[-1])).set_color(RED_G))
            self.play(vline.animate.set_color(RED_G).shift(3.1*LEFT))
            self.play(DrawTxt(P1), DrawTxt(P2), DrawTxt(P3))
            self.wait()
            self.play(ReplacementTransform(curve, curve2), rightuni.animate.set_stroke(color=average_color(Y_G[0], Y_G[-1])).set_color(Y_G), FadeOut(P1, P2, P3, run_time=0.5), vline.animate.set_color(Y_G))
            self.wait()
            f = TexGen(r'f', isMath=True, col=XY_G, font_sz=100).move_to(R)
            R_set = TexGen(r'\{\phantom{(x, y|)} | \phantom{y = x^2|}\}', isMath=True, font_sz=55).move_to(XtimesY)
            xy_obracket = TexGen(r'(', isMath=True, font_sz=55)
            xy_x = TexGen(r'x', isMath=True, font_sz=55).next_to(xy_obracket, buff=0.06)
            xy_comma = TexGen(r',', isMath=True, font_sz=55).next_to(xy_x, buff=0.06).shift(0.16*DOWN)
            xy_y = TexGen(r'y', isMath=True, font_sz=55).next_to(xy_x, aligned_edge=UP, buff=0.33)
            xy_cbracket = TexGen(r')', isMath=True, font_sz=55).next_to(xy_y, buff=0.06).set_y(xy_obracket.get_y())
            xy = VGroup(xy_obracket, xy_x, xy_comma, xy_y, xy_cbracket).move_to(R_set, aligned_edge=LEFT).shift(0.33*RIGHT)
            cond_x2 = TexGen(r'y = x^2', isMath=True, font_sz=55).move_to(R_set, aligned_edge=RIGHT).shift(0.33*LEFT+0.05*UP)
            cond_sin = TexGen(r'y = \sin(x)+1', isMath=True, font_sz=55).move_to([4.35, 0, 0]).shift(0.01*UP)
            self.play(Uncreate(vline))
            self.wait()
            self.play(ReplacementTransform(R, f))
            self.wait()
            self.play(ReplacementTransform(sub, eq), ReplacementTransform(XtimesY, VGroup(R_set, xy)))
            self.wait()
            x2_curve = FunctionGraph(
                lambda t: t**2,
                x_range=[0, 3],
                color=XY_G_R
            ).stretch_to_fit_height(5.98).set_stroke(color=XY_G_R, width=10).move_to(XxY, aligned_edge=DL)
            sin_curve = FunctionGraph(
                lambda t: np.sin(t),
                x_range=[0, 6*PI],
                color=XY_G_R
            ).stretch_to_fit_height(3).stretch_to_fit_width(5.94).set_stroke(color=XY_G_R, width=10).move_to(XxY, aligned_edge=DL).shift(0.01*RIGHT+0.02*UP)
            self.play(ReplacementTransform(curve2, x2_curve), DrawTxt(cond_x2))
            self.wait()
            empty = TexGen(r'\{\}', isMath=True, font_sz=55).move_to(XtimesY)
            self.play(R_set.animate.become(TexGen(r'\{\phantom{(x, y|)} | \phantom{y = \sin(x)+1|}\}', isMath=True, font_sz=55).move_to(XtimesY)), ReplacementTransform(cond_x2, cond_sin), ReplacementTransform(x2_curve, sin_curve), xy.animate.shift(0.93*LEFT))
            self.wait()
            self.play(FadeOut(sin_curve), ReplacementTransform(VGroup(R_set, xy, cond_sin), empty))
            self.wait()
            self.play(FadeOut(x, y, times, XxY, lefttotal, rightuni, eq, x_line, y_line, empty))
            self.play(f.animate.next_to(machine, UP))

        def play_eye():
            f = TexGen(r'f', isMath=True, col=XY_G, font_sz=100).next_to(machine, UP)
            machine_t = TexGen(r'``MACHINE"', font_sz=85, col=BLACK_G).move_to(machine).set_z_index(1)
            in_67 = TexGen(r'67', isMath=True, font_sz=100).next_to(machine, LEFT, buff=1.5)
            out_42 = TexGen(r'42', isMath=True, font_sz=100).next_to(machine).set_x(2)
            vline = Line(start=[2, 1.7, 0], end=[2, -0.7, 0], color=BGRAY_G)
            hline = Line(start=[1.3, 1.2, 0], end=[2.7, 1.2, 0], color=BGRAY_G)
            x = TexGen(r'x', isMath=True, font_sz=42, col=BGRAY_G).move_to([1.6, 1.5, 0])
            y = TexGen(r'y', isMath=True, font_sz=42, col=BGRAY_G).move_to(x, aligned_edge=UP).shift(0.8*RIGHT)
            x1 = TexGen(r'3', isMath=True, font_sz=42, col=BGRAY_G).next_to(x, DOWN).set_y(0.8)
            x2 = TexGen(r'\vdots', isMath=True, font_sz=42, col=BGRAY_G).next_to(x1, 0.85*DOWN)
            x3 = TexGen(r'67', isMath=True, font_sz=42, col=BGRAY_G).next_to(x2, 0.85*DOWN)
            y1 = TexGen(r'4', isMath=True, font_sz=42, col=BGRAY_G).move_to(x1).set_x(y.get_x())
            y2 = TexGen(r'\vdots', isMath=True, font_sz=42, col=BGRAY_G).move_to(x2).set_x(y.get_x())
            y3 = TexGen(r'42', isMath=True, font_sz=42, col=BGRAY_G).move_to(x3).set_x(y.get_x())
            self.add(f)
            self.wait()
            self.play(FadeIn(machine, run_time=0.7))
            self.play(DrawTxt(machine_t), GrowFromCenter(left_stripe, rate_func=linear, run_time=0.6), GrowFromCenter(right_stripe, rate_func=linear, run_time=0.6))
            self.wait()
            self.play(machine.animate.set_fill(opacity=0).set_stroke(color=XY_G, width=5))
            self.remove(machine_t)
            self.play(BounceIn(eye.move_to(machine)))
            self.play(DrawTxt(in_67))
            self.play(in_67.animate.set_x(-2))
            self.play(eye_ball.animate.shift(0.2*LEFT))
            self.play(eye_ball.animate.shift(0.4*RIGHT+0.1*UP), Create(vline), Create(hline),
                      DrawTxt(x), DrawTxt(y), DrawTxt(x1), DrawTxt(x2), DrawTxt(x3), DrawTxt(y1), DrawTxt(y2), DrawTxt(y3))
            self.play(eye_ball.animate.shift(0.2*DOWN))
            self.play(x3.animate.set_stroke(color=average_color(X_G[0], X_G[-1])).set_color(X_G), y3.animate.set_stroke(color=average_color(Y_G[0], Y_G[-1])).set_color(Y_G), run_time=0.5)
            self.play(eye_ball.animate.shift(0.1*UP), ReplacementTransform(y3, out_42), FadeOut(vline, hline, x, y, x1, x2, x3, y1, y2))
            self.play(out_42.animate.next_to(machine, RIGHT, buff=1.5), FadeOut(in_67))
            self.play(eye_ball.animate.shift(0.2*LEFT))
            self.play(FadeOut(out_42))


        # GLOBALS
        machine = RoundedRectangle(corner_radius=0.4, height=3, width=6).set_z_index(-1).set_fill(color=WHITE, opacity=1).set_stroke(color=BLACK).shift(0.5*UP)
        left_stripe = RoundedRectangle(corner_radius=0.1, color=BLACK, height=1, width=0.4).next_to(machine, LEFT, buff=-0.25).set_fill(BLACK, 1)
        right_stripe = deepcopy(left_stripe).next_to(machine, RIGHT, buff=-0.25)
        eye_inner = SVGMobject("eye.svg", height=1)
        eye_ball = Circle(radius=eye_inner.height/2.7, color=BLACK).set_fill(color=BLACK, opacity=1)
        eye_outer = SVGMobject("eye_border.svg", height=1.15)
        eye = VGroup(eye_inner, eye_ball, eye_outer)

        # ANIMATE
        self.wait()
        play_intro()
        play_relation()
        play_love()
        play_func()
        play_eye()
        self.wait()
