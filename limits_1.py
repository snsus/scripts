import cv2
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
        # COLORS
        WHITE_G = color_gradient([WHITE, WHITE], 2)
        BLACK_G = color_gradient([BLACK, BLACK], 2)
        ST_G = color_gradient([ManimColor.from_hex("#FFED95"), ManimColor.from_hex("#FFED95")], 200)
        ST_G = color_gradient([ManimColor.from_hex("#FFD695"), ManimColor.from_hex("#BE722F")], 200)
        LST_G = []
        LST_G.append(color_gradient([ST_G[len(ST_G)//2], ST_G[-1]], 200))
        RST_G = []
        RST_G.append(color_gradient([ST_G[0], ST_G[len(ST_G)//2]], 200))
        for i in range(8):    
            LST_G.append(color_gradient([RST_G[i][len(ST_G)//2], RST_G[i][-1]], 200))
            RST_G.append(color_gradient([RST_G[i][0], RST_G[i][len(ST_G)//2]], 200))
        YEBLUE_G = color_gradient([ManimColor.from_hex("#FFED95"), ManimColor.from_hex("#16E3F9")], 200)
        RYEBLUE_G = color_gradient([ManimColor.from_hex("#16E3F9"), ManimColor.from_hex("#FFED95")], 200)
        GR_G = color_gradient([ManimColor.from_hex("#5F5F5F"), ManimColor.from_hex("#949494")], 200)
        GREEN_G = color_gradient([ManimColor.from_hex("#BFFF97"), ManimColor.from_hex("#00C849")], 200)
        RED_G = color_gradient([ManimColor.from_hex("#FF7490"), ManimColor.from_hex("#FF0033")], 200)
        MAG_G = color_gradient([ManimColor.from_hex("#FFBDFE"), ManimColor.from_hex("#FF68FC")], 200)
        CAUCHY_G = color_gradient([ManimColor.from_hex("#F5F0E9"), ManimColor.from_hex("#756D68")], 200)

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
                
        def Draw(txt, stroke_w=2.0) -> Animation:
            draw_anims = []
            for t in txt:
                draw_anims.append(DrawBorderThenFill(t, stroke_color=t.get_stroke_colors(), stroke_width=stroke_w, run_time=1))
            return draw_anims
        
        def BounceIn(mobjects, run_t=0.5) -> Animation:
            bounce_anims = []
            for mob in mobjects:
                bounce_anims.append(GrowFromCenter(mob, rate_func=rate_functions.ease_out_back, run_time=run_t))
            return bounce_anims
        
        def stickGen(stick):
            left_sticks = VGroup()
            left_fracs = VGroup()
            right_sticks = VGroup()
            right_fracs = VGroup()
            prev_stick = stick
            for i in range(8):
                if i<6:
                    left_sticks.add(RoundedRectangle(corner_radius=0.06, width=prev_stick.width/2, height=stick.height).set_stroke(color=BLACK_G, width=0.001).set_color(LST_G[i]).set_fill(LST_G[i], opacity=1).move_to(prev_stick, aligned_edge=LEFT))
                    right_sticks.add(RoundedRectangle(corner_radius=0.06, width=prev_stick.width/2, height=stick.height).set_stroke(color=BLACK_G, width=0.001).set_color(RST_G[i]).set_fill(RST_G[i], opacity=1).move_to(prev_stick, aligned_edge=RIGHT))
                else:
                    left_sticks.add(RoundedRectangle(corner_radius=0.03, width=prev_stick.width/2, height=stick.height).set_stroke(color=BLACK_G, width=0.000001).set_color(ST_G[0]).set_fill(ST_G[0], opacity=1).move_to(prev_stick, aligned_edge=LEFT))
                    right_sticks.add(RoundedRectangle(corner_radius=0.03, width=prev_stick.width/2, height=stick.height).set_stroke(color=BLACK_G, width=0.000001).set_color(ST_G[0]).set_fill(ST_G[0], opacity=1).move_to(prev_stick, aligned_edge=RIGHT))   
                left_fracs.add(TexGen(rf'\frac{{{1}}}{{{2**(i+1)}}}', isMath=True, col=LST_G[i], font_sz=35).move_to(left_sticks[-1].get_center()).shift(0.6*DOWN))
                right_fracs.add(TexGen(rf'\frac{{{1}}}{{{2**(i+1)}}}', isMath=True, col=RST_G[i], font_sz=35).move_to(right_sticks[-1].get_center()).shift(0.6*DOWN))
                prev_stick = right_sticks[-1]
            left_sticks.add(RoundedRectangle(corner_radius=0.01, width=prev_stick.width/2, height=stick.height-0.001).set_stroke(color=BLACK_G, width=0.000001).set_color(ST_G[0]).set_fill(ST_G[0], opacity=1).move_to(prev_stick, aligned_edge=LEFT))
            right_sticks.add(RoundedRectangle(corner_radius=0.01, width=prev_stick.width/2, height=stick.height-0.001).set_stroke(color=BLACK_G, width=0.000001).set_color(ST_G[0]).set_fill(ST_G[0], opacity=1).move_to(prev_stick, aligned_edge=RIGHT))
            return left_sticks, left_fracs, right_sticks, right_fracs
        
        # Video Segments
        def play_atom(): 
            self.wait()  
            one = TexGen(r'1', isMath=True, font_sz=50, col=ST_G).move_to(stick).shift(0.6*DOWN)
            self.play(GrowFromCenter(stick), run_time=0.5)
            self.play(Draw(one))
            self.wait()
            cut_l = deepcopy(cut_l2cp)        
            self.play(LaggedStart(LaggedStart(Create(cut_l, rate_func=rate_functions.there_and_back), AnimationGroup(Add(l_st[0], r_st[0]), FadeOut(stick, run_time=0)), lag_ratio=0.8, run_time=0.4), AnimationGroup(ReplacementTransform(one, l_fr[0]), ReplacementTransform(deepcopy(one), r_fr[0]), run_time=0.8), lag_ratio=0.45))
            self.wait()
            self.remove(cut_l)
            cut_l = deepcopy(cut_l2cp).set_x(r_fr[0].get_x())
            self.play(LaggedStart(LaggedStart(Create(cut_l, rate_func=rate_functions.there_and_back), AnimationGroup(Add(l_st[1], r_st[1]), FadeOut(r_st[0], run_time=0)), lag_ratio=0.8, run_time=0.4), AnimationGroup(ReplacementTransform(r_fr[0], l_fr[1]), ReplacementTransform(deepcopy(r_fr[0]), r_fr[1]), run_time=0.8), lag_ratio=0.45))
            self.remove(cut_l)
            self.wait()
            cut_l = deepcopy(cut_l2cp).set_x(r_fr[1].get_x())
            self.play(LaggedStart(LaggedStart(Create(cut_l, rate_func=rate_functions.there_and_back), AnimationGroup(Add(l_st[2], r_st[2]), FadeOut(r_st[1], run_time=0)), lag_ratio=0.8, run_time=0.4), AnimationGroup(ReplacementTransform(r_fr[1], l_fr[2]), ReplacementTransform(deepcopy(r_fr[1]), r_fr[2]), run_time=0.8), lag_ratio=0.45))
            self.remove(cut_l)
            self.play(Draw(cuts))
            self.wait()
            for i in range(3, 4):
                cut_l = deepcopy(cut_l2cp).set_x(r_fr[i-1].get_x())
                self.play(LaggedStart(LaggedStart(AnimationGroup(Create(cut_l, rate_func=rate_functions.there_and_back), n_cuts.animate.set_value(n_cuts.get_value()+1).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1]))), AnimationGroup(Add(l_st[i], r_st[i]), FadeOut(r_st[i-1], run_time=0)), lag_ratio=0.8, run_time=0.4), AnimationGroup(ReplacementTransform(r_fr[i-1], l_fr[i]), ReplacementTransform(deepcopy(r_fr[i-1]), r_fr[i]), run_time=0.8), lag_ratio=0.45))
                self.remove(cut_l)
                self.wait(1-i/10)
            cut_l = deepcopy(cut_l2cp).set_x(r_fr[3].get_x())
            self.play(LaggedStart(LaggedStart(AnimationGroup(Create(cut_l, rate_func=rate_functions.there_and_back), n_cuts.animate.set_value(n_cuts.get_value()+1).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1]))), AnimationGroup(Add(l_st[4], r_st[4]), FadeOut(r_st[3], run_time=0)), lag_ratio=0.8, run_time=0.4), AnimationGroup(ReplacementTransform(r_fr[3], dots), run_time=0.4), lag_ratio=0.1))
            self.wait(0.4)
            self.remove(cut_l)
            for i in range(4, 8):
                cut_l = deepcopy(cut_l2cp).set_x(r_fr[i].get_x())
                self.play(LaggedStart(AnimationGroup(Create(cut_l, rate_func=rate_functions.there_and_back), n_cuts.animate.set_value(n_cuts.get_value()+1).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1]))), AnimationGroup(Add(l_st[i+1], r_st[i+1]), FadeOut(r_st[i], run_time=0)), lag_ratio=0.8, run_time=0.4-i/35))
                self.wait(0.4-i/35)
                self.remove(cut_l)
            cut_l = deepcopy(cut_l2cp).set_x(stick.width/2)
            for i in range(8, 32):
                self.play(FadeIn(cut_l), n_cuts.animate.set_value(n_cuts.get_value()+1).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1])), run_time=0.05)
                self.wait(0.05)
                self.remove(cut_l)
                self.wait(0.05)
            explo = VideoMobject("explo.mp4").move_to(cut_l).set_z_index(-10).shift(0.1*LEFT)
            explo.width = 25.1
            self.play(FadeIn(explo, run_time=0.1),
                      r_st[8].animate.rotate(-0.1*PI).shift(15*DL),
                      l_st[8].animate.rotate(0.8*PI).shift(15*UL),
                      l_st[7].animate.rotate(PI/2).shift(15*UL),
                      l_st[6].animate.rotate(-0.2*PI).shift(15*DL),
                      l_st[5].animate.rotate(PI/3).shift(15*UL),
                      l_st[4].animate.rotate(-0.4*PI).shift(15*DL),
                      l_st[3].animate.rotate(0.1*PI).shift(15*UL),
                      l_st[2].animate.rotate(-PI/2).shift(15*DL),
                      l_st[1].animate.rotate(0.4*PI).shift(15*UL),
                      l_st[0].animate.rotate(0.2*PI).shift(15*UL),
                      l_fr[0].animate.rotate(0.1*PI).shift(15*LEFT), 
                      l_fr[1].animate.rotate(-PI/3).shift(15*DL),
                      l_fr[2].animate.rotate(-PI/3).shift(15*DL),
                      l_fr[3].animate.rotate(-0.2*PI).shift(15*DL),
                      dots.animate.rotate(-PI/3).shift(15*DOWN),
                      cuts[0].animate.rotate(-0.1*PI).shift(15*DL),
                      cuts[1].animate.rotate(-0.4*PI).shift(15*DL),
                      cuts[2].animate.rotate(-PI/2).shift(15*DL),
                      run_time=0.55)
            self.wait(8)
    
        def play_proton():
            cut_l = deepcopy(cut_l2cp).set_x(stick.width/2)
            n_cuts.set_value(33).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1]))
            self.add(*(ls for ls in l_st), r_st[8], *(lf for lf in l_fr[0:4]), dots, cuts)
            particles = VideoMobject("particles.mov").move_to(cut_l).shift(0.1*UP+0.7*RIGHT).set_z_index(-1)
            particles.height = 1.5
            self.play(Draw([asu1, A1]))
            self.wait()
            for i in range(32, 49):
                self.play(FadeIn(cut_l), n_cuts.animate.set_value(n_cuts.get_value()+1).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1])), run_time=0.05)
                self.wait(0.05)
                self.remove(cut_l)
                self.wait(0.05)
            self.play(FadeIn(particles))
            self.wait(10)

        def play_planck():
            n_cuts.set_value(50).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1]))
            self.add(*(ls for ls in l_st), r_st[8], *(lf for lf in l_fr[0:4]), dots, A1, asu1, cuts)
            self.play(Draw([asu2, A2]))
            cut_l = deepcopy(cut_l2cp).set_x(stick.width/2)    
            self.add(cut_l)
            n_val = ValueTracker(50)
            n_cuts.add_updater(lambda mob: mob.set_value(n_val.get_value()).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1])))
            self.play(n_val.animate.set_value(116), Blink(cut_l, blinks=66, time_on=0.05, time_off=0.05, hide_at_end=True, run_time=5), run_time=5, rate_func=rate_functions.linear)
            self.wait()
            rip = ImageMobject("rip.png")
            rip.height = 1.4
            rip.to_edge(DOWN, buff=0.1)
            face = ImageMobject("face.png")
            face.height = 1
            face.move_to(rip).shift(1.5*UP).set_z_index(2)
            self.play(FadeIn(rip))
            self.wait()
            self.play(FadeIn(face))
            self.wait()
            self.play(Draw([asu3, A3]))
            self.wait()
            self.play(Group(face, rip).animate.shift(5*DOWN), cuts.animate.set_x(0))
            self.wait()
            cut_l = deepcopy(cut_l2cp).set_x(stick.width/2)
            self.add(cut_l)
            self.play(n_val.animate.set_value(99999999999999999999999999999999999999999), run_time=10, rate_func=rate_functions.linear)
            self.remove(cut_l)
            n_cuts.clear_updaters()
            infty = TexGen(r'\infty', isMath=True, col=YEBLUE_G, font_sz=40).next_to(eq, RIGHT, buff=0.3)
            eq2 = deepcopy(eq).next_to(eq, DOWN).shift(0.3*DOWN).set_color(ST_G)
            l = TexGen(r'l', isMath=True, col=ST_G, font_sz=40).next_to(eq2, LEFT, buff=0.3)
            zero = TexGen(r'0', isMath=True, col=ST_G, font_sz=40).next_to(eq2, RIGHT, buff=0.3)
            self.play(ReplacementTransform(n_cuts, infty), run_time=0.7)
            q = TexGen(r'?', isMath=True, font_sz=130).next_to(VGroup(infty, zero), RIGHT, buff=0.5).shift(0.1*UP)
            self.play(Draw([l, eq2, zero]), run_time=0.7)
            self.play(Draw(q))
            cross = TexGen(r'\ding{55}', col=RED_G, font_sz=130).move_to(VGroup(eq, eq2))
            self.wait()
            self.play(ReplacementTransform(q, cross))
            appro = TexGen(r"``approaches''", font_sz=40, col=YEBLUE_G).move_to(eq)
            appro2 = TexGen(r"``approaches''", font_sz=40, col=ST_G).move_to(eq2)
            self.wait()
            self.play(FadeOut(cross))
            self.play(ReplacementTransform(eq, appro), n.animate.next_to(appro, LEFT, buff=0.3), infty.animate.next_to(appro, RIGHT, buff=0.3))
            self.wait()
            self.play(ReplacementTransform(eq2, appro2), l.animate.next_to(appro2, LEFT, buff=0.3), zero.animate.next_to(appro2, RIGHT, buff=0.3))
            self.wait()
            arr = TexGen(r'\to', isMath=True, font_sz=40, col=YEBLUE_G).move_to(eq)
            arr2 = TexGen(r'\to', isMath=True, font_sz=40, col=ST_G).move_to(eq2)
            self.play(ReplacementTransform(appro, arr), n.animate.next_to(arr, LEFT, buff=0.1), infty.animate.next_to(arr, RIGHT, buff=0.1),
                      ReplacementTransform(appro2, arr2), l.animate.next_to(arr2, LEFT, buff=0.1), zero.animate.next_to(arr2, RIGHT, buff=0.1))
            xarr2 = TexGen(r'\xrightarrow{\phantom{n \to \infty}}', isMath=True, font_sz=62, col=ST_G).move_to(eq2).shift(0.4*UP+0.15*RIGHT)
            self.wait()
            self.play(ReplacementTransform(arr2, xarr2), l.animate.scale(1.6).next_to(xarr2, LEFT, buff=0.15), zero.animate.scale(1.6).next_to(xarr2, RIGHT, buff=0.15))
            self.wait()
            self.play(cuts.animate.shift(0.5*DOWN))
            self.wait()
            lim_eq = TexGen(r'=', isMath=True, font_sz=62, col=ST_G).move_to(xarr2)
            lim = TexGen(r'\lim', isMath=True, font_sz=62, col=ST_G).next_to(l, LEFT, buff=0.15)
            self.wait()
            self.play(ReplacementTransform(xarr2, lim_eq), cuts.animate.shift(0.5*DOWN), Draw(lim), run_time=0.8)
            self.play(lim.animate.shift(0.3*RIGHT+0.05*UP), zero.animate.next_to(lim_eq, RIGHT, buff=0.23).shift(0.02*UP), 
                      cuts.animate.scale(1.1).shift(0.28*UP+1.345*LEFT), l.animate.next_to(lim_eq, LEFT, buff=0.23).shift(0.02*UP), run_time=0.8)
            self.wait()
            n_b = deepcopy(n)
            self.play(VGroup(lim_eq, zero).animate.shift(n.width*1.1*RIGHT), n_b.animate.next_to(l, DR, buff=0.06).shift(0.16*UP), run_time=1)
            self.wait()
            self.play(LaggedStart(deepcopy(l_fr[0]).animate.move_to(VGroup(l, n_b)).fade(darkness=1), 
                                  deepcopy(l_fr[1]).animate.move_to(VGroup(l, n_b)).fade(darkness=1),
                                  deepcopy(l_fr[2]).animate.move_to(VGroup(l, n_b)).fade(darkness=1),
                                  deepcopy(l_fr[3]).animate.move_to(VGroup(l, n_b)).fade(darkness=1),
                                  deepcopy(dots).animate.move_to(VGroup(l, n_b)).fade(darkness=1), lag_ratio=0.6))
            self.wait()
            l_n = TexGen(r'\left(\frac{1}{2}\right)', isMath=True, font_sz=32, col=ST_G).move_to(l, aligned_edge=LEFT)
            self.play(ReplacementTransform(l, l_n), n_b.animate.next_to(l_n, UR, buff=0.06).shift(0.2*DOWN), VGroup(lim_eq, zero).animate.shift(0.4*RIGHT))
            self.wait()
            uarr = TexGen(r'\uparrow', isMath=True).next_to(lim_eq, DOWN)
            self.play(BounceIn(uarr))
            self.wait()
            self.play(FadeOut(uarr))
            q2 = TexGen(r'?', isMath=True, font_sz=80).next_to(zero, RIGHT, buff=0.3)
            self.play(Draw(q2))
            self.wait()
            self.play(FadeOut(A1, asu1, A2, asu2, A3, asu3, lim, cuts, l_n, n_b, zero, lim_eq, q2, *(lf for lf in l_fr[0:4]), dots))
    
        def play_cauchy():
            self.add(*(ls.set_z_index(1) for ls in l_st), r_st[8])
            self.wait()
            ax = Axes(x_range=[0, 15], y_range=[-1, 1, 0.5], axis_config={"include_numbers": False, "include_ticks": False, "tip_shape": StealthTip}, y_length=22, x_length=8.5).next_to(ORIGIN, RIGHT, buff=1).shift(5.5/1.9*DOWN)
            hide_y_line = Line([0, 4, 0], ORIGIN).set_stroke(BLACK, 5, opacity=1).next_to(ax.c2p(0, 0), DOWN, buff=0.01).set_z_index(1)
            self.add(hide_y_line)
            p_dots = VGroup()
            for st in l_st:
                p_dots.add(Dot(st.get_center(), 0.01).set_z_index(-2).set_color(BLACK))
            inf_st = deepcopy(r_st[8])
            p_dots.add(Dot(r_st[8].get_center(), 0.01).set_z_index(-2).set_color(BLACK)) 
            p_dots.add(Dot(inf_st.get_center(), 0.01).set_z_index(-2).set_color(BLACK))
            l_st[0].add_updater(lambda mob: mob.move_to(p_dots[0]))
            l_st[1].add_updater(lambda mob: mob.move_to(p_dots[1]))
            l_st[2].add_updater(lambda mob: mob.move_to(p_dots[2]))
            l_st[3].add_updater(lambda mob: mob.move_to(p_dots[3]))
            l_st[4].add_updater(lambda mob: mob.move_to(p_dots[4]))
            l_st[5].add_updater(lambda mob: mob.move_to(p_dots[5]))
            l_st[6].add_updater(lambda mob: mob.move_to(p_dots[6]))
            l_st[7].add_updater(lambda mob: mob.move_to(p_dots[7]))
            l_st[8].add_updater(lambda mob: mob.move_to(p_dots[8]))
            r_st[8].add_updater(lambda mob: mob.move_to(p_dots[9]))
            inf_st.add_updater(lambda mob: mob.move_to(p_dots[10]))
            self.play(Rotate(l_st[0], -PI/2), p_dots[0].animate.move_to(ax.coords_to_point(1, 1/4)),
                      Rotate(l_st[1], -PI/2), p_dots[1].animate.move_to(ax.coords_to_point(2, 1/8)),
                      Rotate(l_st[2], -PI/2), p_dots[2].animate.move_to(ax.coords_to_point(3, 1/16)),
                      Rotate(l_st[3], -PI/2), p_dots[3].animate.move_to(ax.coords_to_point(4, 1/32)),
                      Rotate(l_st[4], -PI/2), p_dots[4].animate.move_to(ax.coords_to_point(5, 1/64)),
                      Rotate(l_st[5], -PI/2), p_dots[5].animate.move_to(ax.coords_to_point(6, 1/128)),
                      Rotate(l_st[6], -PI/2), p_dots[6].animate.move_to(ax.coords_to_point(7, 1/256)),
                      Rotate(l_st[7], -PI/2), p_dots[7].animate.move_to(ax.coords_to_point(8, 1/512)),
                      Rotate(l_st[8], -PI/2), p_dots[8].animate.move_to(ax.coords_to_point(9, 1/1024)),
                      Rotate(r_st[8], -PI/2), p_dots[9].animate.move_to(ax.coords_to_point(10, 1/2048)),
                      Rotate(inf_st, -PI/2), p_dots[10].animate.move_to(ax.coords_to_point(11, 1/4096)), GrowFromPoint(ax, ax.c2p(0, 0), run_time=1.8))
            self.wait()
            i = 1
            for lf in l_fr:
                lf.next_to(ax.c2p(0, (1/2)**i), LEFT, aligned_edge=DOWN).set_z_index(2)
                i += 1
            ns = VGroup()
            for i in range(1, 11):
                ns.add(TexGen(rf'{i}', font_sz=35, col=YEBLUE_G).next_to(ax.c2p(i, 0), DOWN))
            self.play(LaggedStart(*(BounceIn(nt) for nt in ns), lag_ratio=0.1))
            self.wait()
            hline = DashedLine(ax.c2p(0, 0.5), ax.c2p(12, 0.5)).set_stroke(ST_G, width=3).set_z_index(2)
            hline.save_state()
            l_fr_cp = deepcopy(l_fr)
            self.play(LaggedStart(Create(hline), BounceIn(l_fr[0]), lag_ratio=0.9))
            self.wait(0.5)
            self.play(hline.animate.shift(stick.width/4*DOWN), ReplacementTransform(l_fr[0], l_fr[1]), run_time=1)
            self.wait(0.5)
            self.play(hline.animate.shift(stick.width/8*DOWN), ReplacementTransform(l_fr[1], l_fr[2]), run_time=1)
            self.wait(0.5)
            self.play(hline.animate.shift(stick.width/16*DOWN), ReplacementTransform(l_fr[2], l_fr[3]), run_time=1)
            self.wait(0.5)
            self.play(hline.animate.shift(stick.width/32*DOWN), ReplacementTransform(l_fr[3], l_fr[4]), run_time=1)
            zero_line = Line(ax.c2p(0, 0), ax.c2p(12, 0)).set_stroke(MAG_G, width=3)
            zero = TexGen(r'0', isMath=True, font_sz=35, col=MAG_G).next_to(ax.c2p(0, 0), LEFT, aligned_edge=UP).set_z_index(2)
            self.wait(0.5)
            self.play(Create(zero_line), BounceIn(zero), hline.animate.shift(stick.width/64*DOWN), ReplacementTransform(l_fr[4], l_fr[5]), run_time=1)
            self.wait(0.5)
            self.play(hline.animate.shift(stick.width/128*DOWN), ReplacementTransform(l_fr[5], l_fr[6]), run_time=1)
            self.wait(0.5)
            self.play(hline.animate.shift(stick.width/256*DOWN), ReplacementTransform(l_fr[6], l_fr[7]), run_time=1)
            self.wait()
            self.play(Restore(hline), ReplacementTransform(l_fr[7], l_fr_cp[0]))
            d_arr = DoubleArrow(l_st[0].get_edge_center(DOWN), l_st[0].get_edge_center(UP), tip_shape_start=StealthTip, tip_shape_end=StealthTip, tip_length=0.2).set_x(zero.get_x()).set_stroke(width=4)
            self.play(Create(d_arr))
            self.play(d_arr.animate.put_start_and_end_on(l_st[1].get_edge_center(DOWN)+0.2*UP, l_st[1].get_edge_center(UP)+-0.2*UP).set_x(zero.get_x()).set_stroke(width=4), hline.animate.shift(stick.width/4*DOWN), ReplacementTransform(l_fr_cp[0], l_fr_cp[1]), run_time=1)
            self.wait(0.5)
            self.play(d_arr.animate.put_start_and_end_on(l_st[2].get_edge_center(DOWN)+0.2*UP, l_st[2].get_edge_center(UP)-0.2*UP).set_x(zero.get_x()).set_stroke(width=4), hline.animate.shift(stick.width/8*DOWN), ReplacementTransform(l_fr_cp[1], l_fr_cp[2]), run_time=1)
            self.wait(0.5)
            for i in [0, 1, 3, 4, 5, 6, 7, 8]:
                l_st[i].save_state()
            r_st[8].save_state()
            self.play(*(l_st[i].animate.set_color(GR_G) for i in [0, 1, 3, 4, 5, 6, 7, 8]), r_st[8].animate.set_color(GR_G))
            self.wait()
            d1 = deepcopy(l_fr_cp[2]).move_to([0, 2, 0])
            d_minus = TexGen(r'-', isMath=True, font_sz=35).next_to(d1, RIGHT,  buff=0.25)
            d2 = deepcopy(zero).next_to(d_minus, RIGHT, buff=0.25)
            VGroup(d1, d_minus, d2).next_to(d_arr, LEFT, buff=1)
            self.play(LaggedStart(FadeIn(d1, target_position=l_fr_cp[2]), FadeIn(d_minus, target_position=d_arr), FadeIn(d2, target_position=zero), lag_ratio=0.5), run_time=1.5)
            self.wait()
            dn = TexGen(r'\left(\frac{1}{2}\right)', isMath=True, font_sz=35, col=ST_G).next_to(d_minus, LEFT,  buff=0.25)
            small_n = TexGen(r'n', isMath=True, font_sz=31, col=YEBLUE_G).next_to(dn, RIGHT,  buff=0, aligned_edge=UP).shift(0.02*UP)
            self.play(ReplacementTransform(d1, VGroup(dn, small_n)), *(l_st[i].animate.set_color(LST_G[i]).set_fill(LST_G[i], opacity=1) for i in [0, 1, 3, 4, 5, 6, 7, 8]), r_st[8].animate.set_color(ST_G[0]).set_fill(ST_G[0], opacity=1))
            self.wait()
            self.play(VGroup(dn, small_n, d_minus, d2).animate.set_x(-4))
            neq_zero = TexGen(r'\neq \phantom{|} 0', isMath=True, font_sz=35).next_to(d2, RIGHT, buff=0.25).shift(0.02*DOWN)
            lower = TexGen(r'<', isMath=True, font_sz=35)
            epsi = TexGen(r'\varepsilon', isMath=True, font_sz=35).next_to(lower, RIGHT, buff=0.25, aligned_edge=DOWN)
            leps= VGroup(lower, epsi).next_to(d2, RIGHT,  buff=0.25, aligned_edge=DOWN)
            brc = Brace(VGroup(dn, small_n), DOWN, buff=0.1)
            neq_zero_cp = deepcopy(neq_zero).next_to(brc, DOWN, buff=0.1)
            self.wait()
            self.play(Draw(neq_zero))
            self.wait()
            self.play(Draw([brc, neq_zero_cp]))
            self.wait()
            self.play(FadeOut(brc, neq_zero_cp))
            self.wait()
            down_arr = TexGen(r'\downarrow', isMath=True).next_to(leps, UP).shift(0.23*RIGHT)
            arb_eps = TexGen(r'arbitrarily small\\positive number', font_sz=35).next_to(down_arr, UP)
            epsg = TexGen(r'\varepsilon \phantom{|} > \phantom{|} 0', isMath=True, font_sz=35).next_to(down_arr, UP)
            self.play(LaggedStart(ReplacementTransform(neq_zero, leps), Draw(down_arr), Draw(arb_eps), lag_ratio=0.6), run_time=2.5)
            self.wait()
            self.play(ReplacementTransform(arb_eps, epsg))
            self.wait()
            allfollow = TexGen(r'this and all following', font_sz=35).next_to(VGroup(dn, small_n, d_minus, d2, leps), 2*UP)
            somepoint = TexGen(r'at some cut', font_sz=35).next_to(allfollow, 2*UP)
            nomatter = TexGen(r'no matter which', font_sz=35).next_to(somepoint, 2*UP).shift((epsg.width+0.2)/2*LEFT)
            self.play(epsg.animate.next_to(nomatter, RIGHT, buff=0.2), FadeOut(down_arr), Draw(nomatter))
            self.wait()
            self.play(Draw(somepoint))
            self.wait()
            self.play(Draw(allfollow))
            self.wait()
            self.play(FadeOut(d_arr, l_fr_cp[2], hline))
            eps_line = DashedLine(ax.c2p(0, 0.2), ax.c2p(12, 0.2)).set_stroke(width=3).set_z_index(2)
            eps1 = TexGen(r'\varepsilon = 0.2', isMath=True, font_sz=30).next_to(ax.c2p(0, 0.2), LEFT, aligned_edge=DOWN).set_z_index(2)
            eps2 = TexGen(r'\varepsilon = 0.02', isMath=True, font_sz=30).next_to(ax.c2p(0, 0.02), LEFT, aligned_edge=DOWN).set_z_index(2)
            for ls in l_st[0:6]:
                ls.save_state()
            self.play(LaggedStart(Create(eps_line), BounceIn(eps1), lag_ratio=0.9))
            self.wait()
            ns[2].save_state()
            ns[5].save_state()
            self.play(l_st[0].animate.set_color(GR_G), l_st[1].animate.set_color(GR_G), ns[2].animate.scale(1.8), ns[0].animate.set_color(GR_G), ns[1].animate.set_color(GR_G))
            self.wait()
            self.play(eps_line.animate.shift(ax.c2p(0, 0.02)-ax.c2p(0, 0.2)), ReplacementTransform(eps1, eps2), Restore(ns[2]))
            self.wait()
            self.play(l_st[2].animate.set_color(GR_G), l_st[3].animate.set_color(GR_G), l_st[4].animate.set_color(GR_G), ns[2].animate.set_color(GR_G), ns[3].animate.set_color(GR_G), ns[4].animate.set_color(GR_G), ns[5].animate.scale(1.8))
            self.wait()
            exists = TexGen(r'there exists', font_sz=35)
            N = TexGen(r'N', isMath=True, font_sz=45, col=YEBLUE_G).move_to(ns[5])
            ex_N = TexGen(r'N', isMath=True, font_sz=35, col=YEBLUE_G).next_to(exists, RIGHT, buff=0.25, aligned_edge=DOWN)
            in_N = TexGen(r'\in\phantom{|}\mathbb{N}', font_sz=35, isMath=True).next_to(ex_N, RIGHT, buff=0.17, aligned_edge=DOWN)
            VGroup(exists, ex_N, in_N).move_to(somepoint)
            forall = TexGen(r'for all', font_sz=35)
            ng = TexGen(r'n', isMath=True, font_sz=35, col=YEBLUE_G).next_to(forall, RIGHT, buff=0.25, aligned_edge=DOWN)
            geq = TexGen(r'\geq', isMath=True, font_sz=35).next_to(ng, RIGHT, buff=0.25).align_to(forall, UP)
            gN = TexGen(r'N', isMath=True, font_sz=35, col=YEBLUE_G).next_to(geq, RIGHT, buff=0.25).align_to(forall, DOWN)
            VGroup(forall, ng, geq, gN).move_to(allfollow, aligned_edge=UP)
            self.play(Transform(ns[5], N))
            self.wait()
            self.play(ReplacementTransform(somepoint, exists))
            self.play(LaggedStart(Draw(ex_N), Draw(in_N), lag_ratio=0.7))
            self.wait()
            self.play(ReplacementTransform(allfollow, forall))
            self.play(LaggedStart(Draw(ng), Draw(geq), Draw(gN), lag_ratio=0.7))
            self.wait()
            FA = TexGen(r'\forall', font_sz=35, isMath=True).move_to(forall, aligned_edge=UP)
            EX = TexGen(r'\exists', font_sz=35, isMath=True).next_to(forall, 2*UP).align_to(ex_N, DOWN)
            FA_cp = deepcopy(FA).next_to(EX, 2*UP).align_to(epsg, UP)
            self.play(ReplacementTransform(forall, FA), VGroup(ng, geq, gN).animate.next_to(FA, RIGHT, buff=0.1))
            self.wait()
            self.play(ReplacementTransform(exists, EX), VGroup(ex_N, in_N).animate.next_to(EX, RIGHT, buff=0.1))
            self.wait()
            self.play(ReplacementTransform(nomatter, FA_cp), epsg.animate.next_to(FA_cp, RIGHT, buff=0.1))
            self.wait()
            ddot1 = TexGen(r':', font_sz=30).next_to(gN, RIGHT, buff=0.15, aligned_edge=DOWN)
            ddot2 = deepcopy(ddot1).next_to(in_N, RIGHT, buff=0.15, aligned_edge=DOWN)
            ddot3 = deepcopy(ddot1).next_to(epsg, RIGHT, buff=0.15, aligned_edge=DOWN)
            self.play(Draw([ddot1, ddot2, ddot3]))
            self.play(VGroup(FA, ng, geq, gN, ddot1).animate.next_to(ddot2, RIGHT, buff=0.15).align_to(FA, UP),
                      VGroup(EX, ex_N, in_N, ddot2).animate.move_to(VGroup(FA, ng, geq, gN, ddot1), aligned_edge=DL),
                      VGroup(FA_cp, epsg, ddot3).animate.next_to(FA, LEFT, buff=0.23, aligned_edge=DOWN))
            self.wait()
            self.play(Restore(ns[5]), *(Restore(ls) for ls in l_st[0:6]),
                      ns[0].animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])), 
                      ns[1].animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])), 
                      ns[2].animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      ns[3].animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      ns[4].animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      FadeOut(eps_line, eps2))
            self.wait()
            sn = deepcopy(VGroup(dn, small_n))
            lim = TexGen(r'\lim', font_sz=37, isMath=True).next_to(sn, LEFT, buff=0.35)
            nto = TexGen(r'n', font_sz=30, col=YEBLUE_G, isMath=True)
            toinf = TexGen(r'\to \infty', font_sz=30, isMath=True).scale(0.9).next_to(nto, aligned_edge=DOWN, buff=0.1)
            ntoinf = VGroup(nto, toinf).next_to(lim, DOWN, buff=0.12)
            eq = TexGen(r'=', font_sz=35, isMath=True)
            z = deepcopy(zero).next_to(eq, RIGHT, buff=0.2)
            VGroup(lim, ntoinf).shift(0.08*UP)
            eq_z = VGroup(eq, z).next_to(sn, RIGHT, buff=0.1).align_to(lim, DOWN)
            LIM = VGroup(lim, ntoinf, sn, eq_z).next_to(VGroup(dn, small_n, d_minus, d2, leps), UP).shift(2*UP)
            self.play(Draw(LIM))
            self.wait()
            IF = TexGen(r'IF', font_sz=40).next_to(VGroup(dn, small_n, d_minus, d2, leps), UP).shift(UP).shift(0.25*UP)
            self.play(Draw(IF))
            rect = RoundedRectangle(0.3, width=VGroup(FA_cp, ddot1).width+0.6, height=VGroup(EX, dn).height+0.6).move_to(VGroup(FA_cp, ddot1, EX, dn)).set_stroke(width=2)
            self.play(Create(rect))
            self.wait()
            snew = TexGen(r's', isMath=True, font_sz=42, col=ST_G)
            nnew = deepcopy(small_n).next_to(snew, RIGHT, buff=0).shift(0.15*DOWN)
            seq_new = VGroup(snew, nnew).next_to(VGroup(lim, ntoinf), RIGHT, buff=0.3).shift(0.06*UP)
            seq_new_d = deepcopy(seq_new).next_to(d_minus, LEFT, buff=0.2).shift(0.05*DOWN)
            L_up = TexGen(r'L', isMath=True, font_sz=35, col=MAG_G).move_to(z, aligned_edge=DOWN)
            L_down = deepcopy(L_up).move_to(d2, aligned_edge=DOWN)
            d_minus_cp = deepcopy(d_minus)
            leps_cp = deepcopy(leps)
            VGroup(seq_new_d, d_minus_cp, L_down, leps_cp).set_x(IF.get_x())
            self.play(FadeOut(VGroup(d_minus, d2), run_time=0.6), leps.animate.shift(VGroup(d_minus, d2).width*LEFT))
            log_eps = TexGen(r'\log_{\frac{1}{2}} \left(\varepsilon\right)', isMath=True, font_sz=35).move_to(epsi, aligned_edge=LEFT)
            self.play(ReplacementTransform(epsi, log_eps), Rotate(lower, PI), small_n.animate.scale(1.2).next_to(lower, LEFT, buff=0.25, aligned_edge=DOWN), dn.animate.fade(darkness=1).move_to(log_eps))
            self.play(VGroup(log_eps, lower, small_n).animate.set_x(IF.get_x()))
            self.wait()
            log_eps_cp = deepcopy(log_eps)
            self.play(log_eps.animate.scale(1.3))
            self.wait()
            self.play(ReplacementTransform(log_eps, log_eps_cp))
            self.wait()
            small_n_cp = deepcopy(small_n)
            self.play(small_n.animate.scale(1.3))
            self.wait()
            self.play(ReplacementTransform(small_n, small_n_cp))
            self.wait()
            self.play(VGroup(small_n_cp, lower, log_eps_cp).animate.shift(0.5*UP))
            choose = TexGen(r'choose', font_sz=35)
            chooseN = deepcopy(ex_N).next_to(choose, RIGHT, buff=0.25, aligned_edge=DOWN)
            greater = deepcopy(VGroup(lower, log_eps_cp)).next_to(chooseN, RIGHT, buff=0.2).shift(0.04*DOWN)
            VGroup(choose, chooseN, greater).next_to(VGroup(small_n_cp, lower, log_eps_cp), DOWN, aligned_edge=RIGHT)
            self.play(Draw(choose))
            self.play(Draw([chooseN, greater]))
            self.wait()
            self.play(FadeOut(greater, small_n_cp, choose, chooseN, lower, log_eps_cp, z, sn, *(ls for ls in l_st), r_st[8], zero_line, zero, ns))
            self.wait()
            self.play(Draw([seq_new, L_up, seq_new_d, L_down, d_minus_cp, leps_cp]))
            self.play(VGroup(lim, ntoinf).animate.shift(0.2*RIGHT), VGroup(eq, L_up).animate.shift(0.3*LEFT))
            self.wait()
            left_abs = TexGen(r'|', font_sz=36).next_to(seq_new_d, LEFT, buff=0.1, aligned_edge=DOWN)
            right_abs = deepcopy(left_abs).next_to(L_down, RIGHT, buff=0.1).align_to(left_abs, DOWN)
            self.play(Draw([left_abs, right_abs]), leps_cp.animate.shift(0.15*RIGHT))
            self.wait()
            self.play(hide_y_line.animate.shift(2*DOWN), ax.animate.set_y(1))
            s_dots = VGroup()
            for i in range(1, 23):
                s_dots.add(Dot(ax.c2p(i/1.95, 0.3*np.sin(i)/i**1.1-0.1)).set_color(ST_G).set_stroke(ST_G))
            self.play(LaggedStart(*(BounceIn(d) for d in s_dots), lag_ratio=0.3))
            self.wait()
            L_line = Line(ax.c2p(0, -0.1), ax.c2p(12, -0.1)).set_stroke(MAG_G, width=3).set_z_index(2)
            L = deepcopy(L_up).next_to(ax.c2p(0, -0.1), LEFT).set_z_index(2)
            self.play(Create(L_line), BounceIn(L))
            self.wait()
            eps_up_line = DashedLine(ax.c2p(0, -0.1+0.15), ax.c2p(12, -0.1+0.15)).set_stroke(width=3).set_z_index(2).shift(1.25*DOWN)
            eps_down_line = DashedLine(ax.c2p(0, -0.1-0.15), ax.c2p(12, -0.1-0.15)).set_stroke(width=3).set_z_index(2).shift(1.25*UP)
            eps_up = TexGen(r'L + \varepsilon', font_sz=35, isMath=True).next_to(ax.c2p(0, -0.1+0.15), LEFT, aligned_edge=DOWN).set_z_index(2).shift(1.25*DOWN)
            eps_down = TexGen(r'L - \varepsilon', font_sz=35, isMath=True).next_to(ax.c2p(0, -0.1-0.15), LEFT, aligned_edge=UP).set_z_index(2).shift(1.25*UP)
            self.play(Create(eps_up_line), Create(eps_down_line), BounceIn([eps_up, eps_down]))
            self.wait()
            N = TexGen(r'N', isMath=True, font_sz=35, col=YEBLUE_G).next_to(ax.c2p(0, 0), DOWN, buff=0.2).set_x(s_dots[5].get_x())
            self.play(BounceIn(N), *(s_dots[i].animate.set_color(GR_G).set_stroke(GR_G) for i in range(0, 5)))
            self.wait()
            cauchy = ImageMobject("cauchy.png")
            cauchy.height = 1.8
            cauchy.next_to(lim, 2.4*UP).set_x(IF.get_x())
            augustin = TexGen(r'Augustin-Louis\\Cauchy\\(1789--1857)', font_sz=30, col=CAUCHY_G).next_to(cauchy, LEFT, buff=0.2)
            self.play(BounceIn(cauchy), Draw(augustin))
            brain = ImageMobject("brain.png").shift(3.1*RIGHT)
            brain.height = 2
            brain.align_to(rect, UP).shift(2*UP)
            b_up = DashedLine(ORIGIN, [4, 0, 0]).set_stroke(width=3).set_z_index(2).next_to(brain, UP, buff=0)
            b_down = DashedLine(ORIGIN, [4, 0, 0]).set_stroke(width=3).set_z_index(2).next_to(brain, DOWN, buff=0)
            b_right = DashedLine(ORIGIN, [4, 0, 0]).set_stroke(width=3).set_z_index(2).rotate(PI/2).next_to(brain, RIGHT, buff=0)
            b_left = DashedLine(ORIGIN, [4, 0, 0]).set_stroke(width=3).set_z_index(2).rotate(PI/2).next_to(brain, LEFT, buff=0)
            self.wait()
            self.play(LaggedStart(FadeOut(eps_up, eps_down, s_dots, N, ax, L, L_line), ReplacementTransform(VGroup(eps_up_line, eps_down_line), VGroup(b_up, b_down, b_right, b_left)), GrowFromCenter(brain), lag_ratio=0.9))
            self.wait()            

        def play_conv():
            lim = TexGen(r'\lim_{n \to \infty} s_n =', isMath=True)
            num = TexGen(r'Number', col=MAG_G).next_to(lim, RIGHT, buff=0.21, aligned_edge=UP)
            conv = TexGen(r'$s_n$ converges').next_to(VGroup(lim, num), DOWN, buff=1)
            VGroup(lim, num, conv).move_to([-3.5, 1.5, 0])
            self.play(Draw([lim, num]))
            self.wait()
            self.play(Draw(conv))
            self.wait()
            line = Line([0, 5, 0], [0, -5, 0]).set_color(GR_G).set_stroke(GR_G, width=2)
            lim_div = deepcopy(lim).align_to(lim, UP)
            cases = TexGen(r'\begin{cases}\phantom{\pm \infty} \\ \phantom{\textup{undefined}}\end{cases}', isMath=True, col=MAG_G).next_to(lim_div, RIGHT, buff=0.21).shift(0.11*UP)
            pm_inf = TexGen(r'\pm \infty', isMath=True, col=MAG_G).next_to(cases, RIGHT, buff=0.2).shift(0.4*UP)
            none = TexGen(r'none', col=MAG_G).next_to(cases, RIGHT, buff=0.2).shift(0.4*DOWN)
            div = TexGen(r'$s_n$ diverges').next_to(VGroup(lim_div, cases, pm_inf, none), DOWN).align_to(conv, DOWN)
            VGroup(lim_div, cases, pm_inf, none, div).set_x(3.5)
            self.play(Create(line))
            self.play(Draw(lim_div))
            self.play(GrowFromCenter(cases))
            self.play(Draw(pm_inf))
            self.wait()
            ax_inf = Axes(x_range=[0, 15], y_range=[0, 15], axis_config={"include_numbers": False, "include_ticks": False, "tip_shape": StealthTip, "tip_height": 0.2}, y_length=4, x_length=4).next_to(div, DOWN).align_to(line, LEFT)
            inf_dots = VGroup()
            for i in range(1, 30):
                inf_dots.add(Dot(ax_inf.c2p(i, 0.03*i**2+1)))
            inf_line = Line(ax_inf.c2p(0, 0.05+1), ax_inf.c2p(40, 0.05+1)).set_stroke(MAG_G, width=3)
            inf_line2 = Line(ax_inf.c2p(0, 0.05+1), ax_inf.c2p(40, 0.05+1)).set_stroke(MAG_G, width=3).set_y(5)
            self.play(LaggedStart(*(BounceIn(d) for d in inf_dots), lag_ratio=0.5, run_time=2), ReplacementTransform(inf_line, inf_line2, run_time=2, rate_func=rate_functions.ease_in_quad))
            self.play(FadeOut(inf_dots))
            self.wait()
            self.play(Draw(none))
            self.wait()
            ax_alt = Axes(x_range=[0, 7], y_range=[-7, 7], axis_config={"include_numbers": False, "include_ticks": False, "tip_shape": StealthTip, "tip_height": 0.2}, y_length=4, x_length=4).next_to(div, DOWN).align_to(line, LEFT)
            alt_dots = VGroup()
            for i in range(1, 20):
                alt_dots.add(Dot(ax_alt.c2p(i, (-1)**i*3)))
            alt_line = deepcopy(inf_line).set_y(alt_dots[0].get_y())
            for d in alt_dots:
                if d == alt_dots[-1]:
                    self.play(BounceIn(d), alt_line.animate.set_y(d.get_y()).fade(darkness=1), run_time=0.4)
                else:
                    self.play(BounceIn(d), alt_line.animate.set_y(d.get_y()), run_time=0.4)
            self.wait()
            self.play(FadeOut(alt_dots))
            self.play(Draw(div))
            self.wait()
            conv_def_up = TexGen(r"\forall \varepsilon > 0: \exists N \in \mathbb{N}: \forall n \geq N:", isMath=True).next_to(conv, DOWN).shift(1.5*DOWN)
            conv_sn = TexGen(r'|s_n-\phantom{\textup{Number}}|', isMath=True)
            num_cp = deepcopy(num).move_to(conv_sn, aligned_edge=RIGHT).shift(0.1*LEFT+0.04*UP)
            conv_leps = TexGen(r'< \varepsilon', isMath=True).next_to(num_cp, aligned_edge=DOWN, buff=0.3)
            conv_def_down = VGroup(conv_sn, num_cp, conv_leps).next_to(conv_def_up, DOWN)
            div_def_up = deepcopy(conv_def_up).set_x(div.get_x())
            div_sn = TexGen(r'|s_n-\phantom{L}|', isMath=True)
            L = TexGen(r'L', col=MAG_G).move_to(div_sn, aligned_edge=RIGHT).shift(0.1*LEFT+0.04*UP)
            div_leps = deepcopy(conv_leps).next_to(L, aligned_edge=DOWN, buff=0.3)
            div_def_down = VGroup(div_sn, L, div_leps).next_to(div_def_up, DOWN)
            conv_rect = RoundedRectangle(0.3, width=VGroup(conv_def_up, conv_def_down).width+0.5, height=VGroup(conv_def_up, conv_def_down).height+0.5).move_to(VGroup(conv_def_up, conv_def_down)).set_stroke(GREEN_G)
            div_rect = deepcopy(conv_rect).rotate(PI).move_to(VGroup(div_def_up, div_def_down))
            asu = TexGen(r'\mathbb{A}:', isMath=True, col=GREEN_G).next_to(div_rect, UP)
            contra = TexGen(r'$\Rightarrow$ Contradiction', col=RED_G).next_to(div_rect, DOWN) 
            self.play(Draw(VGroup(conv_def_up, conv_def_down)))
            self.play(Create(conv_rect))
            self.wait()
            self.play(Draw(asu))
            self.play(Draw(VGroup(div_def_up, div_def_down)), Create(div_rect))
            self.wait()
            self.play(Draw(contra))
            self.wait()
            self.play(FadeOut(contra, asu), div_rect.animate.set_stroke(RED_G))
            self.wait()

        def play_div():
            sn_eq_n = TexGen(r's_n = n', isMath=True).to_edge(UP, buff=0.5)
            ax = Axes(x_range=[0, 10], y_range=[0, 10], axis_config={"include_numbers": False, "include_ticks": False, "tip_shape": StealthTip, "tip_height": 0.2}, y_length=4, x_length=4)
            n_dots = VGroup()
            for i in range(1, 11):
                n_dots.add(Dot(ax.c2p(i, i)))
            self.play(Draw(sn_eq_n))
            self.wait()
            self.play(GrowFromPoint(ax, ax.c2p(0, 0)))
            self.play(LaggedStart(*(BounceIn(d) for d in n_dots), lag_ratio=0.6))
            self.wait()
            divs = TexGen(r'diverges').next_to(sn_eq_n, DOWN)
            self.play(FadeOut(n_dots, ax))
            self.play(Draw(divs))
            proof = TexGen(r'Proof.', isMath=True).next_to(divs, DOWN).to_edge(LEFT, buff=1)
            asu = TexGen(r'\mathbb{A}:', isMath=True, col=GREEN_G).next_to(proof, DOWN, aligned_edge=LEFT)
            self.wait()
            self.play(Draw(proof))
            self.wait()
            self.play(Draw(asu))
            self.wait()
            conv_up = TexGen(r"\forall \varepsilon > 0: \exists N \in \mathbb{N}: \forall n \geq N:", isMath=True).next_to(asu, RIGHT, buff=0.5, aligned_edge=UP)
            conv_down = TexGen(r'|n-L|<\varepsilon', isMath=True).next_to(conv_up, DOWN)
            self.play(Draw(conv_up))
            self.play(Draw(conv_down))
            self.wait()
            eps1 = TexGen(r'\varepsilon = 1:', isMath=True).next_to(conv_down, DOWN).to_edge(LEFT, buff=1)
            absd = TexGen(r'|\phantom{n-L}|', isMath=True)
            nminL = TexGen(r'n-L', isMath=True).move_to(absd)
            leps = TexGen(r'< 1', isMath=True).next_to(absd, RIGHT, buff=0.25).align_to(nminL, DOWN)
            VGroup(absd, nminL, leps).next_to(eps1, DOWN).align_to(conv_down, LEFT)
            minus1 = TexGen(r'-1 <', isMath=True).next_to(absd, LEFT, buff=0.25).align_to(nminL, DOWN)
            self.play(Draw(eps1))
            self.wait()
            self.play(Draw(VGroup(absd, nminL, leps)))
            self.wait()
            self.play(FadeOut(absd))
            self.play(Draw(minus1))
            self.wait()
            brace = Brace(VGroup(nminL, leps))
            self.play(GrowFromCenter(brace))
            self.wait()
            n = TexGen(r'n', isMath=True).next_to(nminL, DOWN, aligned_edge=LEFT)
            oneplusL = TexGen(r'1+L', isMath=True).next_to(leps, DOWN, aligned_edge=RIGHT).align_to(n, DOWN).shift(0.03*DOWN)
            l = TexGen(r'<', isMath=True).next_to(n, RIGHT, buff=0.25, aligned_edge=DOWN)
            nsmallerL = VGroup(n, l, oneplusL).next_to(brace, DOWN)
            ngreatern = VGroup(deepcopy(n), TexGen(r'>', isMath=True).next_to(n, RIGHT, buff=0.25, aligned_edge=DOWN), deepcopy(oneplusL)).next_to(nsmallerL, DOWN)
            self.play(Draw(nsmallerL))
            self.wait()
            oneplusL_cp = deepcopy(oneplusL)
            self.play(oneplusL.animate.scale(1.2).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.wait()
            n_cp = deepcopy(n)
            self.play(ReplacementTransform(oneplusL, oneplusL_cp), n.animate.scale(1.2).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.wait()
            self.play(ReplacementTransform(n, n_cp))
            exists_n = TexGen(r'\exists n \geq N:', isMath=True).next_to(nsmallerL, DOWN).to_edge(LEFT, buff=1)
            self.play(Draw(exists_n))
            self.play(Draw(ngreatern))
            contra_rect = RoundedRectangle(0.2, width=VGroup(l, ngreatern[1]).width+0.3, height=VGroup(l, ngreatern[1]).height+0.3).set_stroke(RED_G, width=2).move_to(VGroup(l, ngreatern[1]))
            self.wait()
            self.play(Create(contra_rect))
            contra = TexGen(r'$\Rightarrow$ Contradiction', col=RED_G).next_to(ngreatern, RIGHT, buff=0.5) 
            qed = TexGen(r'q.e.d.', isMath=True).next_to(contra, DR)
            self.wait()
            self.play(Draw(contra))
            self.play(Draw(qed))
            self.wait()

        def play_plan():
            s_n = TexGen(r's_n', isMath=True).to_edge(UP, buff=1)
            theo = TexGen(r'Theorem', col=GR_G).shift(1.5*UP+15*RIGHT)
            theos = VGroup()
            theos.add(deepcopy(theo).next_to(theo, RIGHT, buff=1))
            for i in range(0, 11):
                theos.add(deepcopy(theo).next_to(theos[i], RIGHT, buff=1))
            self.play(Draw(s_n))
            line = Line(s_n.get_edge_center(DOWN)-[0, 0.2, 0], s_n.get_edge_center(DOWN)-[0, 0.9, 0])
            self.play(LaggedStart(AnimationGroup(theos.animate.shift(44.9*LEFT), run_time=5, rate_func=rate_functions.smoothererstep), Create(line, run_time=0.7), lag_ratio=0.85))
            self.play(theos[9].animate.scale(1.3).set_color(WHITE_G).set_stroke(WHITE_G), run_time=0.7)
            self.wait()
            more = VGroup(TexGen(r'Infinite Sums $\sum$').shift(0.5*DOWN))
            more.add(TexGen(r"Limits of $f$").next_to(more[-1], 2*DOWN))
            more.add(TexGen(r"Derivatives $f'$ and Integrals $\int$").next_to(more[-1], 2*DOWN))
            more.add(TexGen(r'$\ldots$').next_to(more[-1], 3*DOWN))
            self.play(LaggedStart(*(BounceIn(m) for m in more), lag_ratio=0.7), run_time=2)
            self.wait()


        # GLOBALS
        stick = RoundedRectangle(corner_radius=0.06, width=11, height=0.25).set_stroke(color=BLACK_G, width=0.001).set_color(ST_G).set_fill(ST_G, opacity=1)
        cut_l2cp = Line([0, 1, 0], [0, -1, 0]).set_stroke(YEBLUE_G, width=3).set_z_index(1)
        l_st, l_fr, r_st, r_fr = stickGen(stick) 
        dots = TexGen(r'\ldots', isMath=True, font_sz=30, col=LST_G[7]).move_to(r_fr[3], aligned_edge=DOWN)
        asu1 = TexGen(r'$\mathbb{A}$:', font_sz=40, col=GREEN_G).to_edge(UP, buff=1).align_to(stick, LEFT)
        asu2 = deepcopy(asu1).next_to(asu1, DOWN)
        asu3 = deepcopy(asu1).next_to(asu2, DOWN)
        A1 = TexGen(r'Splitting atoms is harmless', font_sz=40).next_to(asu1, RIGHT, aligned_edge=UP, buff=0.3)
        A2 = TexGen(r'Quantum Chromodynamics is a lie', font_sz=40).next_to(asu2, RIGHT, aligned_edge=UP, buff=0.3)
        A3 = TexGen(r'Max Planck is a lie',font_sz=40).next_to(asu3, RIGHT, aligned_edge=UP, buff=0.3)
        eq = TexGen(r'=', isMath=True, font_sz=40, col=YEBLUE_G).shift(1.9*DOWN)
        n = TexGen(r'n', col=YEBLUE_G, isMath=True, font_sz=40).next_to(eq, LEFT, buff=0.3)      
        n_cuts = DecimalNumber(3, num_decimal_places=0, font_size=42, stroke_width=1, group_with_commas=False).next_to(eq, RIGHT, buff=0.3).align_to(n, DOWN).set_color(RYEBLUE_G).set_stroke(color=average_color(RYEBLUE_G[0], RYEBLUE_G[-1]))
        cuts = VGroup(n, eq, n_cuts).align_to(stick, RIGHT)
        
        # ANIMATE
        play_atom()
        play_proton()
        play_planck()
        play_cauchy()
        play_conv()
        play_div()
        play_plan()
