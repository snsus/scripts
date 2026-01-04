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
        YELL_G = color_gradient([ManimColor.from_hex("#FEFE99"), ManimColor.from_hex("#FFC655")], 200)
        GRAY_G = color_gradient([ManimColor.from_hex("#B1B1B1"), ManimColor.from_hex("#B1B1B1")], 200)
        MAGENTA_G = color_gradient([ManimColor.from_hex("#FF90FF"), ManimColor.from_hex("#8000FF")], 200)
        HMAGENTA_G = color_gradient([ManimColor.from_hex("#FFACFF"), ManimColor.from_hex("#B061FF")], 200)
        SIN_G = color_gradient([ManimColor.from_hex("#00E5FF"), ManimColor.from_hex("#004CFF")], 200)
        COS_G = color_gradient([ManimColor.from_hex("#BFFF97"), ManimColor.from_hex("#00C849")], 200)
        RED_G = color_gradient([ManimColor.from_hex("#FF7490"), ManimColor.from_hex("#FF0033")], 200)
        RRED_TMP = color_gradient([RED_G[-1], RED_G[0]], 200)
        RRED_G = color_gradient([RED_G[0], RED_G[-1], RED_G[0]], 200)

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
            T_l1 = Line(start=[-2, 0, 0], end=[2, 0, 0])
            T_l2 = Line(start=T_l1.get_last_point(), end=T_l1.start).rotate(-np.pi/3, about_point=T_l1.get_last_point())
            T_l3 = Line(start=T_l2.get_last_point(), end=T_l1.start)
            Trig = VGroup(T_l1, T_l2, T_l3).set_stroke(width=5).set_color(YELL_G)
            Trig.shift(-Trig.get_center_of_mass())
            T = Triangle().set_color(YELL_G).set_stroke(width=9).scale(4).rotate(2*PI/3, about_point=ORIGIN).move_to(ORIGIN)
            T.height=Trig.height
            T.move_to(Trig)
            ax_wave = Axes(
                x_range=[0, 4*PI],
                y_range=[-1, 1],
                x_length=12,
                y_length=4,
                tips=True,
                axis_config={'tip_shape': StealthTip, 'include_ticks': True, 'tip_height': 0.2}
            )
            wv = ParametricFunction(function=lambda t: ax_wave.c2p(t, np.sin(2*t)), t_range=[0, 4*PI]).set_color(YELL_G).set_stroke(width=9)
            drop = ImageMobject('drop.jpg')
            earth = ImageMobject('eqrth.jpg')
            sound = ImageMobject('sound.jpg')
            light = ImageMobject('light.jpg')
            gravi = ImageMobject('gravi.webp')
            earth.height = 10
            drop.height = 9
            sound.height = 10
            light.height = 10
            gravi.height = 10
            self.play(FadeIn(drop))
            self.wait()
            self.play(FadeOut(drop), FadeIn(earth))
            self.wait()
            self.play(FadeOut(earth), FadeIn(sound))
            self.wait()
            self.play(FadeOut(sound), FadeIn(light))
            self.wait()
            self.play(FadeOut(light))
            self.play(Create(wv), run_time=4)
            self.play(ReplacementTransform(wv, T, path_func=path_along_arc(PI/2)), run_time=3)
            self.wait(0.5)
            self.play(DrawTxt(TexGen(r'?', isMath=True, font_sz=222, col=YELL_G).move_to(T.get_center_of_mass())))

        def play_angle():
            T_l1 = Line(start=[-2, 0, 0], end=[2, 0, 0])
            T_l2 = Line(start=T_l1.get_last_point(), end=T_l1.start).rotate(-np.pi/3, about_point=T_l1.get_last_point())
            T_l3 = Line(start=T_l2.get_last_point(), end=T_l1.start)
            Trig = VGroup(T_l1, T_l2, T_l3).set_stroke(width=5).set_color(YELL_G)
            Trig.shift(-Trig.get_center_of_mass())
            #
            self.play(Create(Trig))
            self.wait()
            self.play(Trig.animate.scale(1.8), run_time=1.5, rate_func=there_and_back)
            self.play(Rotate(Trig, PI/3, about_point=Trig.get_center_of_mass()), run_time=1.5, rate_func=there_and_back)
            #
            T_l2.add_updater(lambda mob: mob.put_start_and_end_on(start=T_l1.get_last_point(), end=T_l3.get_start()))
            #
            self.play(T_l3.animate.put_start_and_end_on(start=T_l2.get_last_point()-[4, 0, 0], end=T_l1.get_start()), run_time=1.5, rate_func=there_and_back)
            self.wait()
            #
            coolmoji.move_to(Trig.get_center_of_mass()).shift(RIGHT*4)
            question = TexGen(r'?', isMath=False, font_sz=130).next_to(coolmoji)
            babylon = ImageMobject('babylon.webp')
            babylon.height = 2*T_l2.get_y() - 2*T_l1.get_y()
            babylon.next_to(Trig, LEFT, buff=0).shift(2*RIGHT).set_z_index(-2)
            rect_around_babylon = RectAroundImage(babylon)
            baby_year = TexGen(r'Babylonier\\ $\thicksim$ 4000 Jahre her', isMath=False, font_sz=50).next_to(rect_around_babylon, UP)
            T_l2.suspend_updating()
            black_rect_up = Rectangle(color=BLACK, height=5, width=babylon.width+1).set_fill(BLACK, opacity=1).next_to(rect_around_babylon, UP, buff=0).set_z_index(-1)
            black_rect_down = deepcopy(black_rect_up).next_to(rect_around_babylon, DOWN, buff=0).set_z_index(-1)
            #
            self.add(black_rect_up, black_rect_down)
            self.play(BounceIn(coolmoji), DrawTxt(question))
            self.wait()
            self.play(Trig.animate.shift(4*RIGHT), FadeOut(question), FadeIn(babylon, rect_around_babylon, target_position=[-6, 2, 0]))
            self.play(DrawTxt(baby_year))
            self.wait()
            ##
            T_l1_mirror = Line(start=T_l1.get_last_point(), end=T_l1.get_start())
            T_l2_mirror = Line(start=T_l2.get_last_point(), end=T_l2.get_start())
            T_l3_mirror = Line(start=T_l1.get_start(), end=T_l2.get_last_point())
            Ang = Angle(T_l1, T_l3_mirror, radius=1)
            Ang = Angle(T_l1, T_l3_mirror, radius=1)
            Ang2 = Angle(T_l2, T_l1_mirror, radius=1)
            Ang3 = Angle(T_l3, T_l2_mirror, radius=1)
            start_angle = 0
            num_divisions = 60
            dividing_lines = VGroup()
            for i in range(1, num_divisions):
                new_angle = start_angle + i * (Ang.get_value() / num_divisions)
                new_line = Line(T_l1.get_start(), Ang.get_start()+[0.03, 0, 0], color=WHITE).rotate(new_angle, about_point=T_l1.get_start()).set_stroke(width=0.5)
                dividing_lines.add(new_line)
            #
            u_arrow = TexGen(r'\uparrow', isMath=True).next_to(T_l1.get_start()+[0.57, 0, 0], DOWN)
            s_font = 50
            default_Ang = TexGen(r'1 Winkel', font_sz=s_font).next_to(u_arrow, DOWN, buff=0.1)
            #
            self.wait()
            self.play(Create(Ang))
            self.play(DrawTxt(u_arrow), DrawTxt(default_Ang))
            self.wait()
            self.play(Create(Ang2), Create(Ang3))
            self.wait()
            self.play(FadeOut(Ang2, Ang3))
            self.wait()
            #
            numerals = ImageMobject('nums.png')
            numerals.width = babylon.width
            numerals.next_to(babylon, UP, buff=0).set_z_index(-2)
            base60 = TexGen(r'Basis 60\\(Sexagesimal System)', isMath=False, font_sz=50).next_to(rect_around_babylon, UP)
            #
            self.play(babylon.animate.shift(babylon.height*1.02*DOWN).add_to_back(), numerals.animate.shift(babylon.height*1.02*DOWN), ReplacementTransform(baby_year, base60))
            self.remove(babylon)
            self.wait()
            #
            clock = ImageMobject('clock.png')
            clock.height =  1
            clock.next_to(rect_around_babylon, DOWN)
            entspricht = TexGen(r'$\widehat{=}$', font_sz=s_font).next_to(clock, DOWN)
            one_hour = TexGen(r'1 Stunde',font_sz=s_font).next_to(entspricht, LEFT)
            minutes = TexGen(r'60 Minuten', font_sz=s_font).next_to(entspricht, RIGHT)
            hour_full = VGroup(one_hour, entspricht, minutes)
            entspricht_cp = deepcopy(entspricht).next_to(entspricht, DOWN)
            one_minute = TexGen(r'1 Minute', font_sz=s_font).next_to(entspricht_cp, LEFT)
            seconds = TexGen(r'60 Sekunden', font_sz=s_font).next_to(entspricht_cp, RIGHT)
            minute_full = VGroup(one_minute, entspricht_cp, seconds)
            #
            self.play(BounceIn(clock))
            self.wait()
            self.play(DrawTxt(hour_full))
            self.play(DrawTxt(minute_full))
            self.wait()
            #
            one_angle_eq60 = TexGen(r'1 Winkel $\widehat{=}$ 60', font_sz=s_font).move_to(default_Ang)
            deg = TexGen(r'°', font_sz=s_font).next_to(one_angle_eq60, buff=0.05).shift(0.11*UP)
            CAM.save_state()
            T_l1.save_state()
            T_l3.save_state()
            Ang.save_state()
            #
            self.play(CAM.animate.move_to(Ang.get_center_of_mass()).scale(0.14), T_l1.animate.set_stroke(width=0.9), T_l3.animate.set_stroke(width=0.9), Ang.animate.set_stroke(width=0.9))
            self.wait()
            self.play(LaggedStartMap(FadeIn, dividing_lines))
            self.wait()
            self.play(Restore(CAM), Restore(T_l1), Restore(T_l3), Restore(Ang))
            self.wait()
            self.play(ReplacementTransform(default_Ang, one_angle_eq60))
            self.wait()
            self.play(DrawTxt(deg))
            self.wait()
            #
            T_l2.clear_updaters()
            Trig_to_rotate = VGroup(Trig, Ang, dividing_lines)
            #
            self.play(FadeOut(coolmoji))
            self.play(Trig_to_rotate.animate.scale_to_fit_width(2).move_to([4, rect_around_babylon.get_y(), 0], aligned_edge=DOWN), FadeOut(one_angle_eq60, deg, u_arrow))
            Trig_rot1 = deepcopy(Trig_to_rotate)
            self.play(Rotate(Trig_rot1, PI/3, about_point=T_l1.get_start()), run_time=0.4)
            Trig_rot2 = deepcopy(Trig_rot1)
            self.play(Rotate(Trig_rot2, PI/3, about_point=T_l1.get_start()), run_time=0.4)
            Trig_rot3 = deepcopy(Trig_rot2)
            self.play(Rotate(Trig_rot3, PI/3, about_point=T_l1.get_start()), run_time=0.4)
            Trig_rot4 = deepcopy(Trig_rot3)
            self.play(Rotate(Trig_rot4, PI/3, about_point=T_l1.get_start()), run_time=0.4)
            Trig_rot5 = deepcopy(Trig_rot4)
            self.play(Rotate(Trig_rot5, PI/3, about_point=T_l1.get_start()), run_time=0.4)
            self.wait()
            #
            one_circ_eq = TexGen(r'1 Kreis $\widehat{=}$ 6 $\cdot$ 60°', font_sz=s_font).next_to(Trig_rot4, DOWN).shift(0.08*LEFT)
            Circ_baby = Circle(radius=0.5).move_to(T_l1.get_start()).set_color(WHITE).set_stroke(color=WHITE)
            fingers = ImageMobject('fingers.png')
            fingers.height = 1.5
            angry.height = 1.5
            fingers.shift(2.5*UP)
            black_rect_mid = Rectangle(color=BLACK, height=3.5, width=6.5).set_fill(BLACK, opacity=1)
            black_rect_mid.move_to(rect_around_babylon)
            #
            self.play(DrawTxt(one_circ_eq))
            self.wait()
            self.add(Circ_baby)
            self.play(FadeIn(black_rect_mid), FadeOut(base60,Trig_rot1, Trig_rot2, Trig_rot3, Trig_rot4, Trig_rot5))
            self.remove(numerals, rect_around_babylon, black_rect_mid)
            self.play(clock.animate.shift(2.5*UP), one_circ_eq.animate.next_to(Circ_baby, DOWN).shift(0.08*LEFT),
                      hour_full.animate.shift(2.5*UP), minute_full.animate.shift(2.5*UP))
            self.wait()
            self.play(BounceIn(fingers))
            self.wait()
            self.play(FadeIn(angry), FadeOut(fingers), run_time=0.5)
            self.wait()
            #
            entspricht_cp2 = deepcopy(entspricht).next_to(entspricht_cp, DOWN)
            one_second = TexGen(r'1 Sekunde', font_sz=s_font).next_to(entspricht_cp2, LEFT)
            millisecs = TexGen(r'1000 Millisekunden', font_sz=s_font).next_to(entspricht_cp2, RIGHT)
            second_full = VGroup(one_second, entspricht_cp2, millisecs)
            entspricht_cp3 = deepcopy(entspricht).next_to(entspricht_cp2, DOWN)
            one_millisec = TexGen(r'1 Millisekunde', font_sz=s_font).next_to(entspricht_cp3, LEFT)
            mikrosecs = TexGen(r'1000 Mikrosekunden', font_sz=s_font).next_to(entspricht_cp3, RIGHT)
            millisec_full = VGroup(one_millisec, entspricht_cp3, mikrosecs)
            vdots = TexGen(r'\vdots', isMath=True).next_to(entspricht_cp3, DOWN)
            #
            self.play(DrawTxt(second_full))
            self.play(DrawTxt(millisec_full))
            self.play(DrawTxt(vdots))
            self.wait()
            self.play(FadeOut(clock, hour_full, minute_full, second_full, millisec_full, vdots))
            self.wait()
            self.play(FadeOut(Ang, dividing_lines, one_circ_eq), run_time=0.5)
            self.play(FadeOut(Trig, run_time=0.3), Circ_baby.animate.move_to([-3, -1, 0]).scale(2))
            self.wait()
            #
            u_circ = deepcopy(Circ_baby).set_stroke(width=5.5).set_color(RED_G)
            frac_line = Line(start=[-0.35, -1, 0], end=[0.35, -1, 0]).set_stroke(width=4.5)
            umfang = TexGen(r'U', col=RED_G, font_sz=70, isMath=True).move_to([-1.5, -1, 0])
            diam = TexGen(r'd', col=MAGENTA_G, font_sz=70, isMath=True).move_to([-3, -1.5, 0])
            diam_line = Line(start=[-4, -1, 0], end=[-2, -1, 0]).set_color(MAGENTA_G).set_stroke(width=5.5)
            eq_pi = TexGen(r'= \pi', font_sz=70, isMath=True)
            eq_pi.add_updater(lambda mob: mob.next_to(frac_line, buff=0.3))
            #
            self.play(Create(u_circ))
            self.play(DrawTxt(umfang))
            self.remove(Circ_baby)
            self.wait()
            self.play(umfang.animate.next_to(frac_line, UP))
            umfang.add_updater(lambda mob: mob.next_to(frac_line, UP))
            self.play(BounceIn(frac_line))
            self.play(Create(diam_line))
            self.play(DrawTxt(diam))
            self.wait()
            self.play(diam.animate.next_to(frac_line, DOWN))
            diam.add_updater(lambda mob: mob.next_to(frac_line, DOWN))
            self.wait()
            self.play(DrawTxt(eq_pi))
            self.wait()
            self.play(u_circ.animate.scale(2).set_stroke(width=6), diam_line.animate.scale(2).set_stroke(width=6), 
                      umfang.animate.scale(2), diam.animate.scale(2), run_time=3, rate_func=there_and_back)
            self.wait()
            #
            radius_line = Line(start=[-3, -1, 0], end=[-2, -1, 0]).set_color(HMAGENTA_G).set_stroke(width=5)
            eq_zwei_pi = TexGen(r'= 2 \pi', font_sz=70, isMath=True)
            radius = TexGen(r'r', col=HMAGENTA_G, font_sz=70, isMath=True).move_to([-2.5, -1.4, 0])
            radius_cp = deepcopy(radius).next_to(eq_zwei_pi, aligned_edge=DOWN, buff=0.05)
            #
            umfang.clear_updaters()
            diam.clear_updaters()
            self.play(FadeOut(frac_line, run_time=0.1), umfang.animate.next_to(eq_pi, LEFT, aligned_edge=DOWN), diam.animate.next_to(eq_pi, aligned_edge=DOWN, buff=0.05))
            self.wait()
            #
            eq_zwei_pi_r = VGroup(eq_zwei_pi, radius_cp).next_to(umfang, aligned_edge=DOWN)
            eins = TexGen(r'1', col=HMAGENTA_G, font_sz=68, isMath=True).move_to([-2.5, -1.4, 0])
            mpunkt = Dot([-3, -1, 0], color=HMAGENTA_G[-1])
            #
            self.play(ReplacementTransform(diam_line, radius_line), BounceIn(mpunkt))
            self.play(DrawTxt(radius), ReplacementTransform(VGroup(eq_pi, diam), eq_zwei_pi_r))
            self.wait()
            self.play(ReplacementTransform(radius, eins))
            self.play(ShrinkToCenter(radius_cp, run_time=0.3))
            self.wait()
            #
            unit_circ = VGroup(u_circ, mpunkt)
            unit_circ_txt = TexGen(r'Einheitskreis').next_to(unit_circ, UP, buff=0.5)
            u_zwei_pi = VGroup(umfang, eq_zwei_pi)
            #
            self.play(unit_circ.animate.set_color(WHITE), u_zwei_pi.animate.set_color(WHITE).scale(0.8).next_to(unit_circ, DOWN, buff=0.5), FadeOut(eins, radius_line))
            self.wait()
            self.play(DrawTxt(unit_circ_txt))
            self.wait()
            #
            ang_l1 = Line(start=[2, -1, 0], end=[4.5, -1, 0]).set_stroke(width=5).set_color(YELL_G)
            ang_l2 = deepcopy(ang_l1).rotate(PI/3, about_point=ang_l1.get_start()).set_stroke(width=5).set_color(YELL_G)
            Ang = Angle(ang_l1, ang_l2, radius=2.5)
            self.play(Create(ang_l1), Create(ang_l2))
            start_angle = 0
            num_divisions = 360
            dividing_lines = VGroup()
            for i in range(1, num_divisions):
                new_angle = start_angle + i * (Ang.get_value() / 60)
                new_line = Line(ang_l1.get_start(), Ang.get_start()+[0.03, 0, 0], color=WHITE).rotate(new_angle, about_point=ang_l1.get_start()).set_stroke(width=0.9)
                dividing_lines.add(new_line)
            self.play(LaggedStartMap(FadeIn, dividing_lines[0:60]))
            #
            deg_track = ValueTracker(60)
            deg_txt = DecimalNumber(deg_track.get_value(), 0, font_size=58).move_to([3.25, 2, 0])
            deg_txt.add_updater(lambda mob: mob.set_value(deg_track.get_value()).move_to([3.25, 2, 0]))
            deg_unit = TexGen(r'°', font_sz=55)
            deg_unit.add_updater(lambda mob: mob.next_to(deg_txt, RIGHT, aligned_edge=UP, buff=0.05))
            Ang_60 = Angle(ang_l1, ang_l2, radius=1).set_stroke(width=6.5).set_color(RED_G)
            ang_entspricht = TexGen(r'\widehat{=}', isMath=True, col=RED_G, font_sz=55).next_to(deg_txt, buff=0.35)
            Ang_60_txt = TexGen(r'\frac{2\pi}{6}', isMath=True, col=RED_G, font_sz=55).next_to(ang_entspricht)
            Ang_60_txt2 = TexGen(r'\frac{\pi}{3}', isMath=True, col=RED_G, font_sz=55).next_to(ang_entspricht)
            #
            self.play(FadeIn(deg_txt, deg_unit))
            self.wait()
            self.play(u_zwei_pi.animate.next_to(unit_circ_txt, DOWN), unit_circ.animate.move_to(ang_l1.get_start()))
            self.wait()
            self.play(Create(Ang_60))
            self.wait()
            self.play(DrawTxt(ang_entspricht.next_to(deg_txt, buff=0.35)), DrawTxt(Ang_60_txt))
            self.wait()
            self.play(ReplacementTransform(Ang_60_txt, Ang_60_txt2))
            self.wait()
            self.play(FadeOut(ang_entspricht, Ang_60_txt2, Ang_60))
            self.play(ang_l2.animate.rotate(PI/6, about_point=ang_l1.get_start()), LaggedStartMap(FadeIn, dividing_lines[60:90], run_time=1.4), deg_track.animate.set_value(90), rate_func=linear)
            #
            Ang_90 = Angle(ang_l1, ang_l2, radius=1, dot=True).set_stroke(width=6.5).set_color(RED_G)
            Ang_90_txt = TexGen(r'\frac{2\pi}{4}', isMath=True, col=RED_G, font_sz=55).next_to(ang_entspricht)
            Ang_90_txt2 = TexGen(r'\frac{\pi}{2}', isMath=True, col=RED_G, font_sz=55).next_to(ang_entspricht)
            #
            self.play(Create(Ang_90))
            self.play(DrawTxt(ang_entspricht.next_to(deg_txt, buff=0.35)), DrawTxt(Ang_90_txt))
            self.wait()
            self.play(ReplacementTransform(Ang_90_txt, Ang_90_txt2))
            self.wait()
            self.play(FadeOut(ang_entspricht, Ang_90_txt2, Ang_90))
            self.play(Rotate(ang_l2, 3*PI/2, about_point=ang_l1.get_start(), run_time=2), LaggedStartMap(FadeIn, dividing_lines[90:360], run_time=2.8), deg_track.animate.set_value(360), run_time=2, rate_func=linear)
            #
            circ_360 = deepcopy(u_circ).set_stroke(width=6.5).set_color(RED_G)
            Ang_360_txt = TexGen(r' 2\pi', isMath=True, col=RED_G, font_sz=55)
            #
            self.play(Create(circ_360))
            self.play(DrawTxt(ang_entspricht.next_to(deg_txt, buff=0.35)), DrawTxt(Ang_360_txt.next_to(ang_entspricht, buff=0.2)))
            self.wait()
            self.remove(unit_circ)
            
        def play_triangle():
            T_l1 = Line(start=[-2, -2.5, 0], end=[2, -2.5, 0])
            T_l2 = Line(start=T_l1.get_last_point(), end=T_l1.start).rotate(-np.pi/3, about_point=T_l1.get_last_point())
            T_l3 = Line(start=T_l2.get_last_point(), end=T_l1.start)
            Trig = VGroup(T_l1, T_l2, T_l3).set_stroke(width=5).set_color(YELL_G)
            last_point_l2 = T_l2.get_last_point()
            #
            self.play(BounceIn(angry))
            self.play(Create(Trig))
            T_l2.add_updater(lambda mob: mob.put_start_and_end_on(start=T_l1.get_last_point(), end=T_l3.get_start()))
            self.play(BounceIn(coolmoji.move_to(Trig.get_center_of_mass())))
            self.wait()
            self.play(T_l3.animate.put_start_and_end_on(start=[2, 1.5, 0], end=T_l1.get_start()), coolmoji.animate.move_to([0.8, -1.2, 0]))
            #
            T_l1_mirror = Line(start=T_l1.get_last_point(), end=T_l1.get_start())
            R_Ang = Angle(T_l1_mirror, T_l2, dot=True, radius=0.5,other_angle=True)
            a = TexGen(r'a', isMath=True, font_sz=80).next_to(T_l1, DOWN)
            b = TexGen(r'b', isMath=True,font_sz=80).next_to(T_l2, RIGHT)
            c = TexGen(r'c', isMath=True, font_sz=80).next_to(T_l3.get_center(), LEFT, buff=0.5)
            pythagoras = TexGen(r'Pythagoras', font_sz=80).move_to([-4, 1.5, 0])
            satz = TexGen(r'a^2+b^2=c^2', isMath=True, font_sz=80).next_to(pythagoras, DOWN)
            #
            self.play(Create(R_Ang))
            self.wait()
            self.play(DrawTxt(a), DrawTxt(b), DrawTxt(c))
            self.wait()
            self.play(DrawTxt(pythagoras), DrawTxt(satz))
            self.wait()
            self.play(FadeOut(coolmoji, a, b, c, pythagoras, satz, R_Ang))
            self.play(T_l3.animate.put_start_and_end_on(start=last_point_l2, end=T_l1.get_start()))
            self.wait()
            #
            T_l1_mirror_half = Line(start=T_l1.get_center(), end=T_l1.get_start())
            div_line = Line(start=last_point_l2, end=T_l1.get_center())
            div_line_mirror = Line(start=T_l1.get_center(), end=last_point_l2)
            R_Ang2 = Angle(T_l1_mirror_half, div_line_mirror, dot=True, radius=0.5,other_angle=True)
            #
            self.play(Create(div_line))
            self.play(Create(R_Ang2))
            self.wait()
            self.play(FadeOut(angry, R_Ang2, div_line, Trig))

        def play_trig():
            trigono = TexGen(r'Trigono', font_sz=100)
            metry = TexGen(r'metry', font_sz=100).next_to(trigono, buff=0.08).shift(0.037*DOWN)
            trigonometry = VGroup(trigono, metry).move_to(ORIGIN)
            strich = TexGen(r'-', font_sz=100).next_to(metry, LEFT).shift(0.1*DOWN)
            T_l1 = Line(start=[-1.5, 1, 0], end=[1.5, 1, 0])
            T_l2 = Line(start=T_l1.get_last_point(), end=[1.5, 4, 0])
            T_l3 = Line(start=T_l2.get_last_point(), end=T_l1.start)
            T_l1_mirror = Line(start=T_l1.get_last_point(), end=T_l1.get_start())
            R_Ang_ref = Angle(T_l1_mirror, T_l2, dot=True, radius=0.6, other_angle=True).shift(0.5*DOWN)
            Trig = VGroup(T_l1, T_l2, T_l3).set_stroke(width=5).next_to(strich, LEFT)
            T_l1_mirror2 = Line(start=T_l1.get_last_point(), end=T_l1.get_start())
            R_Ang = Angle(T_l1_mirror2, T_l2, dot=True, radius=0.6, other_angle=True)
            #
            self.play(DrawTxt(trigonometry))
            self.wait()
            self.play(ReplacementTransform(trigono, VGroup(Trig, strich, R_Ang)))
            self.wait()
            self.play(FadeOut(metry, strich), Trig.animate.move_to([0, 2, 0]), R_Ang.animate.move_to(R_Ang_ref))
            self.wait()
            #
            hypo = TexGen(r'Hypotenuse').next_to(T_l3.get_center(), LEFT, buff=0.5).shift(0.3*UP+0.4*RIGHT)
            kat = TexGen(r'Leg').next_to(T_l1, DOWN)
            kat_cp = deepcopy(kat).next_to(T_l2)
            #
            self.play(Wiggle(T_l3))
            self.play(DrawTxt(hypo))
            self.wait()
            self.play(Wiggle(T_l1), Wiggle(T_l2))
            self.play(DrawTxt(kat), DrawTxt(kat_cp))
            self.wait()
            #
            T_l3_mirror = Line(start=T_l3.get_last_point(), end=T_l3.get_start())
            Ang_alpha = Angle(T_l1, T_l3_mirror, radius=1.5)
            ref_trig_alpha = VGroup(Line(start=T_l1.get_start(), end=Ang_alpha.get_start()), Line(start=T_l1.get_start(), end=Ang_alpha.get_last_point()), Line(start=Ang_alpha.get_start(), end=Ang_alpha.get_last_point()))
            alpha = TexGen(r'\alpha', isMath=True).move_to(ref_trig_alpha.get_center_of_mass())
            ankat = TexGen(r'Adjacent Leg', col=COS_G).next_to(T_l1, DOWN)
            gegenkat = TexGen(r'Opposite Leg', col=SIN_G).next_to(T_l2)
            #
            self.play(Create(Ang_alpha), DrawTxt(alpha))
            self.wait()
            self.play(T_l2.animate.set_color(SIN_G))
            self.play(ReplacementTransform(kat_cp, gegenkat))
            self.play(T_l1.animate.set_color(COS_G))
            self.play(ReplacementTransform(kat, ankat))
            self.wait()
            #
            T_l2_mirror = Line(start=T_l2.get_last_point(), end=T_l2.get_start())
            Ang_beta = Angle(T_l2_mirror, T_l3, radius=1.5, other_angle=True)
            ref_trig_beta = VGroup(Line(start=T_l3.get_start(), end=Ang_beta.get_start()), Line(start=T_l3.get_start(), end=Ang_alpha.get_last_point()), Line(start=Ang_beta.get_start(), end=Ang_beta.get_last_point()))
            beta = TexGen(r'\beta', isMath=True).move_to(ref_trig_beta.get_center_of_mass()).shift(0.05*RIGHT+0.05*UP)
            #
            self.play(FadeOut(alpha, Ang_alpha), Create(Ang_beta), DrawTxt(beta))
            self.play(ankat.animate.next_to(T_l2), gegenkat.animate.next_to(T_l1, DOWN), T_l1.animate.set_color(SIN_G), T_l2.animate.set_color(COS_G))
            self.wait()
            self.play(FadeOut(beta, Ang_beta), Create(Ang_alpha), DrawTxt(alpha))
            self.play(ankat.animate.next_to(T_l1, DOWN), gegenkat.animate.next_to(T_l2), T_l1.animate.set_color(COS_G), T_l2.animate.set_color(SIN_G))
            self.wait()
            #
            H = TexGen(r'H').next_to(T_l3.get_center(), LEFT, buff=0.5).shift(0.3*UP+0.4*RIGHT)
            G = TexGen(r'O', col=SIN_G).next_to(T_l2)
            A = TexGen(r'A', col=COS_G).next_to(T_l1, DOWN)
            #
            self.play(ReplacementTransform(hypo, H), ReplacementTransform(gegenkat, G), ReplacementTransform(ankat, A))
            self.play(FadeOut(R_Ang))
            self.wait()
            #
            sin_frac = Line(start=[-5.3, -2, 0], end=[-4.7, -2, 0]).move_to([-5, -2, 0])
            sin_G = deepcopy(G).next_to(sin_frac, UP)
            sin_H = deepcopy(H).next_to(sin_frac, DOWN)
            cos_frac = Line(start=[-3.3, -2, 0], end=[-2.7, -2, 0]).move_to([-3, -2, 0])
            cos_A = deepcopy(A).next_to(cos_frac, UP)
            cos_H = deepcopy(H).next_to(cos_frac, DOWN)
            tan_frac = Line(start=[-1.3, -2, 0], end=[-0.7, -2, 0]).move_to([-1, -2, 0])
            tan_G = deepcopy(G).next_to(tan_frac, UP)
            tan_A = deepcopy(A).next_to(tan_frac, DOWN)
            cot_frac = Line(start=[0.7, -2, 0], end=[1.3, -2, 0]).move_to([1, -2, 0])
            cot_A = deepcopy(A).next_to(cot_frac, UP)
            cot_G = deepcopy(G).next_to(cot_frac, DOWN)
            sec_frac = Line(start=[2.7, -2, 0], end=[3.3, -2, 0]).move_to([3, -2, 0])
            sec_H = deepcopy(H).next_to(sec_frac, UP)
            sec_A = deepcopy(A).next_to(sec_frac, DOWN)
            csc_frac = Line(start=[4.7, -2, 0], end=[5.3, -2, 0]).move_to([5, -2, 0])
            csc_H = deepcopy(H).next_to(csc_frac, UP)
            csc_G = deepcopy(G).next_to(csc_frac, DOWN)
            #
            self.play(FadeIn(sin_frac), FadeIn(sin_G, target_position=G.get_center()), FadeIn(sin_H, target_position=H.get_center()),
                      FadeIn(cos_frac), FadeIn(cos_A, target_position=A.get_center()), FadeIn(cos_H, target_position=H.get_center()),
                      FadeIn(tan_frac), FadeIn(tan_G, target_position=G.get_center()), FadeIn(tan_A, target_position=A.get_center()),
                      FadeIn(cot_frac), FadeIn(cot_A, target_position=A.get_center()), FadeIn(cot_G, target_position=G.get_center()),
                      FadeIn(sec_frac), FadeIn(sec_H, target_position=H.get_center()), FadeIn(sec_A, target_position=A.get_center()),
                      FadeIn(csc_frac), FadeIn(csc_H, target_position=H.get_center()), FadeIn(csc_G, target_position=G.get_center()))
            self.wait()
            #
            sin_pack = VGroup(sin_frac, sin_G, sin_H)
            cos_pack = VGroup(cos_frac, cos_A, cos_H)
            tan_pack = VGroup(tan_frac, tan_G, tan_A)
            Trig_pack = VGroup(Trig, H, A, G, alpha, Ang_alpha)
            sin_pack.save_state()
            cos_pack.save_state()
            tan_pack.save_state()
            Trig_pack.save_state()
            #
            self.play(sin_pack.animate.shift(4.5*UP), Trig_pack.animate.move_to([3, 0, 0]), cos_pack.animate.move_to([-5, 0, 0]), tan_pack.animate.move_to([-5, -2.5, 0]), 
                      FadeOut(cot_frac, cot_A, cot_G, sec_frac, sec_A, sec_H, csc_frac, csc_G, csc_H))
            self.wait()
            #
            sin_track = ValueTracker(3/np.sqrt(18))
            cos_track = ValueTracker(3/np.sqrt(18))
            tan_track = ValueTracker(1)
            eq_sin = TexGen(r'=', isMath=True, font_sz=55).next_to(sin_frac, buff=0.2)
            eq_cos = TexGen(r'=', isMath=True, font_sz=55).next_to(cos_frac, buff=0.2)
            eq_tan = TexGen(r'=', isMath=True, font_sz=55).next_to(tan_frac, buff=0.2)
            sin_val = DecimalNumber(sin_track.get_value(), 2, font_size=55, show_ellipsis=True)
            cos_val = DecimalNumber(cos_track.get_value(), 2, font_size=55, show_ellipsis=True)
            tan_val = DecimalNumber(tan_track.get_value(), 2, font_size=55, show_ellipsis=True)
            sin_G.add_updater(lambda mob: mob.next_to(sin_frac, UP))
            sin_H.add_updater(lambda mob: mob.next_to(sin_frac, DOWN))
            cos_A.add_updater(lambda mob: mob.next_to(cos_frac, UP))
            cos_H.add_updater(lambda mob: mob.next_to(cos_frac, DOWN))
            tan_G.add_updater(lambda mob: mob.next_to(tan_frac, UP))
            tan_A.add_updater(lambda mob: mob.next_to(tan_frac, DOWN))
            sin_val.add_updater(lambda mob: mob.set_value(sin_track.get_value()).next_to(eq_sin, buff=0.2))
            cos_val.add_updater(lambda mob: mob.set_value(cos_track.get_value()).next_to(eq_cos, buff=0.2))
            tan_val.add_updater(lambda mob: mob.set_value(tan_track.get_value()).next_to(eq_tan, buff=0.2))
            #
            self.play(FadeIn(eq_sin, sin_val, eq_cos, cos_val, eq_tan, tan_val))
            self.play(Trig_pack.animate.scale(2), sin_G.animate.scale(2), sin_H.animate.scale(2),
                      cos_A.animate.scale(2), cos_H.animate.scale(2), tan_G.animate.scale(2), tan_A.animate.scale(2), rate_func=there_and_back, run_time=3)
            self.wait()
            #
            T_l2.add_updater(lambda mob: mob.put_start_and_end_on(start=T_l1.get_last_point(), end=T_l3.get_start()))
            A.add_updater(lambda mob: mob.next_to(T_l1, DOWN))
            G.add_updater(lambda mob: mob.next_to(T_l2))
            H.add_updater(lambda mob: mob.next_to(T_l3.get_center(), LEFT, buff=0.5).shift(0.3*UP+0.4*RIGHT))
            lock = ImageMobject('lock.png')
            lock.height = 0.35
            sin_lock = deepcopy(lock).next_to(sin_H, LEFT, buff=0.1)
            cos_lock = deepcopy(lock).next_to(cos_H, LEFT, buff=0.1)
            sec_lock = deepcopy(lock).next_to(sec_H, LEFT, buff=0.1)
            csc_lock = deepcopy(lock).next_to(csc_H, LEFT, buff=0.1)
            lock.add_updater(lambda mob: mob.next_to(H, LEFT, buff=0.1))
            sin_lock.add_updater(lambda mob: mob.next_to(sin_H, LEFT, buff=0.1))
            cos_lock.add_updater(lambda mob: mob.next_to(cos_H, LEFT, buff=0.1))
            Ang_alpha_new = Angle(T_l1, deepcopy(T_l3).put_start_and_end_on(start=T_l3.get_last_point(), end=T_l3.get_start()).rotate(PI/8, about_point=T_l1.get_start()), radius=1.5)
            ref_trig_alpha_new = VGroup(Line(start=T_l1.get_start(), end=Ang_alpha_new.get_start()), Line(start=T_l1.get_start(), end=Ang_alpha_new.get_last_point()), Line(start=Ang_alpha_new.get_start(), end=Ang_alpha_new.get_last_point()))
            #
            self.play(BounceIn(lock), BounceIn(sin_lock), BounceIn(cos_lock))
            self.wait()
            T_l1.save_state()
            T_l3.save_state()
            alpha.save_state()
            Ang_alpha.save_state()
            G.save_state()
            A.save_state()
            H.save_state()
            sin_G.save_state()
            cos_A.save_state()
            tan_A.save_state()
            tan_G.save_state()
            sin_track.save_state()
            cos_track.save_state()
            tan_track.save_state()
            self.play(Rotate(T_l3, PI/8, about_point=T_l1.get_start()), Ang_alpha.animate.become(Ang_alpha_new), alpha.animate.scale(1.5).move_to(ref_trig_alpha_new.get_center_of_mass()),
                      T_l1.animate.put_start_and_end_on(start=T_l1.get_start(), end=T_l1.get_start() + [np.sqrt(18)*np.cos(3*np.pi/8), 0, 0]), 
                      sin_track.animate.set_value(np.sin(3*np.pi/8)), cos_track.animate.set_value(np.cos(3*np.pi/8)), tan_track.animate.set_value(np.tan(3*np.pi/8)),
                      G.animate.scale(1.5), sin_G.animate.scale(1.5), A.animate.scale(0.7), cos_A.animate.scale(0.7),
                      tan_G.animate.scale(1.5), tan_A.animate.scale(0.7), run_time=3, rate_func=linear)
            self.wait(2)
            self.play(Restore(T_l1), Restore(T_l3), Restore(Ang_alpha), Restore(alpha), 
                      Restore(A), Restore(G), Restore(H), Restore(sin_G), Restore(cos_A), Restore(tan_A), Restore(tan_G), 
                      sin_track.animate.set_value(2/np.sqrt(8)), cos_track.animate.set_value(2/np.sqrt(8)), tan_track.animate.set_value(1), run_time=2, rate_func=linear)
            self.wait()
            T_l2.clear_updaters()
            self.play(sin_frac.animate.move_to([-5, -2, 0]), Restore(H), cos_frac.animate.move_to([-3, -2, 0]), tan_frac.animate.move_to([-1, -2, 0]), Restore(Trig_pack), FadeOut(sin_val, cos_val, tan_val, eq_sin, eq_cos, eq_tan),
                      FadeIn(cot_A, cot_frac, cot_G, sec_A, sec_frac, sec_H, csc_frac, csc_G, csc_H, sec_lock, csc_lock))
            self.wait()
            #
            f_alpha_sin = TexGen(r'f(\alpha)', isMath=True).next_to(sin_H, DOWN, buff=0.5)
            f_alpha_cos = deepcopy(f_alpha_sin).next_to(cos_H, DOWN, buff=0.5)
            f_alpha_tan = deepcopy(f_alpha_sin).next_to(tan_A, DOWN, buff=0.5)
            f_alpha_cot = deepcopy(f_alpha_sin).next_to(cot_G, DOWN, buff=0.5)
            f_alpha_sec = deepcopy(f_alpha_sin).next_to(sec_A, DOWN, buff=0.5)
            f_alpha_csc = deepcopy(f_alpha_sin).next_to(csc_G, DOWN, buff=0.5)
            sin_alpha = TexGen(r'\sin(\alpha)', isMath=True).next_to(sin_H, DOWN, buff=0.5)
            cos_alpha = TexGen(r'\cos(\alpha)', isMath=True).next_to(cos_H, DOWN, buff=0.5)
            tan_alpha = TexGen(r'\tan(\alpha)', isMath=True).next_to(tan_A, DOWN, buff=0.5)
            cot_alpha = TexGen(r'\cot(\alpha)', isMath=True).next_to(cot_G, DOWN, buff=0.5)
            sec_alpha = TexGen(r'\sec(\alpha)', isMath=True).next_to(sec_A, DOWN, buff=0.5)
            csc_alpha = TexGen(r'\csc(\alpha)', isMath=True).next_to(csc_G, DOWN, buff=0.5)
            #
            self.play(FadeIn(f_alpha_sin, target_position=sin_frac), FadeIn(f_alpha_cos, target_position=cos_frac), FadeIn(f_alpha_tan, target_position=tan_frac),
                      FadeIn(f_alpha_cot, target_position=cot_frac), FadeIn(f_alpha_sec, target_position=sec_frac), FadeIn(f_alpha_csc, target_position=csc_frac))
            self.wait()
            self.play(ReplacementTransform(f_alpha_sin, sin_alpha), ReplacementTransform(f_alpha_cos, cos_alpha), ReplacementTransform(f_alpha_tan, tan_alpha),
                      ReplacementTransform(f_alpha_cot, cot_alpha), ReplacementTransform(f_alpha_sec, sec_alpha), ReplacementTransform(f_alpha_csc, csc_alpha))
            self.wait()
            #
            eins_H = TexGen(r'1', isMath=True).move_to(H)
            sin_eins = deepcopy(eins_H).move_to(sin_H)
            cos_eins = deepcopy(eins_H).move_to(cos_H)
            sec_eins = deepcopy(eins_H).move_to(sec_H)
            csc_eins = deepcopy(eins_H).move_to(csc_H)
            Trig_pack = VGroup(T_l1, T_l2, T_l3, Ang_alpha, alpha)
            sin_lock.clear_updaters()
            cos_lock.clear_updaters()
            lock.clear_updaters()
            sin_G.clear_updaters()
            cos_A.clear_updaters()
            #
            self.play(ReplacementTransform(H, eins_H), ReplacementTransform(sin_H, sin_eins), ReplacementTransform(cos_H, cos_eins),
                      ReplacementTransform(sec_H, sec_eins), ReplacementTransform(csc_H, csc_eins),
                      Trig_pack.animate.scale_to_fit_width(1/np.sqrt(2)))
            self.wait()
            self.play(FadeOut(lock, sin_lock, cos_lock, csc_lock, sec_lock, sin_frac, cos_frac, sin_eins, cos_eins), sin_G.animate.shift(0.5*DOWN), sin_alpha.animate.set_color(SIN_G).set_stroke(color=average_color(SIN_G[0], SIN_G[-1])), cos_A.animate.shift(0.5*DOWN), cos_alpha.animate.set_color(COS_G).set_stroke(color=average_color(COS_G[0], COS_G[-1])))
            self.wait()
            #
            tan_sin = deepcopy(sin_alpha).move_to(tan_G)
            tan_cos = deepcopy(cos_alpha).move_to(tan_A)
            cot_sin = deepcopy(sin_alpha).move_to(cot_G)
            cot_cos = deepcopy(cos_alpha).move_to(cot_A)
            sec_cos = deepcopy(cos_alpha).move_to(sec_A)
            csc_sin = deepcopy(sin_alpha).move_to(csc_G)
            eq_sin_2 = TexGen(r'=', isMath=True).next_to(G)
            eq_cos_2 = TexGen(r'=', isMath=True).next_to(A)
            #
            self.play(ReplacementTransform(tan_G, tan_sin), ReplacementTransform(tan_A, tan_cos), ReplacementTransform(cot_G, cot_sin),
                      ReplacementTransform(cot_A, cot_cos), ReplacementTransform(sec_A, sec_cos), ReplacementTransform(csc_G, csc_sin),
                      tan_frac.animate.scale(2.4), cot_frac.animate.scale(2.4), sec_frac.animate.scale(2.4), csc_frac.animate.scale(2.4))
            self.wait()
            self.play(FadeIn(eq_sin_2), FadeIn(eq_cos_2), FadeOut(sin_G, cos_A),
                      sin_alpha.animate.next_to(eq_sin_2, RIGHT), cos_alpha.animate.next_to(eq_cos_2, RIGHT))
            self.wait()
            self.play(FadeOut(tan_alpha, sec_alpha, cot_alpha, csc_alpha, tan_sin, tan_cos, tan_frac, sec_cos, sec_eins, sec_frac,
                              cot_cos, cot_sin, cot_frac, sec_cos, sec_eins, sec_frac, csc_sin, csc_frac, csc_eins))
            self.wait()
            self.play(sin_alpha.animate.move_to(G, aligned_edge=LEFT), cos_alpha.animate.move_to(A), FadeOut(eq_cos_2, eq_sin_2, G, A, run_time=0.5))
            self.wait()
            #
            circ = Circle(radius=1).set_color(WHITE).set_stroke(color=WHITE, width=5).move_to(T_l1.get_start()).shift(3*LEFT)
            m = Dot(circ.get_center())
            schablone = VGroup(circ, m)
            #
            self.play(Create(schablone))
            self.wait()
            self.play(schablone.animate.move_to(T_l1.get_start()), FadeOut(eins_H), FadeOut(sin_alpha, cos_alpha))
            self.wait()
            #
            T_l3_mirror2 = Line(start=T_l3.get_last_point(), end=T_l3.get_start())
            Ang_45 = Angle(T_l1, T_l3_mirror2, radius=1).set_color(RED_G).set_stroke(width=5.5)
            alpha_2 = TexGen(r'\alpha', isMath=True, col=RED_G).next_to(Ang_45).shift(0.1*UP+0.1*LEFT)
            #
            self.play(Create(Ang_45),ReplacementTransform(alpha, alpha_2), FadeOut(Ang_alpha, run_time=0.1))
            self.wait()
            #
            circ_stuff = VGroup(circ, T_l1, T_l2, T_l3)
            #
            self.play(circ_stuff.animate.move_to([-4, 2, 0]), FadeOut(Ang_45, alpha_2, m, run_time=0.1))
            self.wait()

        def play_wave():
            T_l1 = Line(start=[-4, 2, 0], end=[-4+1/np.sqrt(2), 2, 0]).set_color(COS_G).set_stroke(width=5)
            T_l2 = Line(start=T_l1.get_last_point(), end=T_l1.get_last_point()+[0, 1/np.sqrt(2), 0]).set_color(SIN_G).set_stroke(width=5)
            T_l3 = Line(start=T_l1.get_start(), end=T_l2.get_last_point()).set_stroke(width=5)
            circ = Circle(radius=1).set_color(WHITE).set_stroke(color=WHITE, width=5).move_to([-4, 2, 0])
            self.add(T_l1, circ, T_l2, T_l3)
            ax_sin = Axes(
                x_range=[0, 2*PI+0.5, PI/4],
                y_range=[-1.5, 1.5, 1],
                x_length=2*PI+0.5,
                y_length=3,
                tips=True,
                axis_config={'tip_shape': StealthTip, 'include_ticks': True, 'tip_height': 0.2}
            ).next_to(circ, buff=1)
            sin_xticks = ax_sin.get_x_axis().get_tick_marks()
            sin_yticks = ax_sin.get_y_axis().get_tick_marks()
            one_pi = TexGen(r'\pi', isMath=True, font_sz=35).next_to(sin_xticks[3], DOWN, buff=0.1)
            two_pi = TexGen(r'2\pi', isMath=True, font_sz=35).next_to(sin_xticks[-1], DOWN, buff=0.1)
            one = TexGen(r'1', isMath=True, font_sz=35).next_to(sin_yticks[1], LEFT, buff=0.1)
            mone = TexGen(r'-1', isMath=True, font_sz=35).next_to(sin_yticks[0], LEFT, buff=0.1)
            #
            self.wait()
            self.play(Create(ax_sin), run_time=3)
            self.play(DrawTxt(one_pi), DrawTxt(two_pi), DrawTxt(one), DrawTxt(mone))
            self.wait()
            #
            ang = ValueTracker(PI/4)
            arc = Arc(radius=1, start_angle=0, angle=ang.get_value(), arc_center=circ.get_center()).set_stroke(width=5.5).set_color(RED_G)
            Ang_line = Line(start=ax_sin.get_origin(), end=ax_sin.get_origin()+[ang.get_value(), 0, 0]).set_stroke(width=5.5).set_color(RRED_TMP)
            #
            self.play(Create(arc))
            tmp_arc = deepcopy(arc)
            self.play(ReplacementTransform(tmp_arc, Ang_line, run_time=1.5))
            self.wait()
            Ang_line.add_updater(lambda mob: mob.put_start_and_end_on(start=ax_sin.get_origin(), end=ax_sin.get_origin()+[ang.get_value(), 0, 0]).set_stroke(width=5.5).set_color(RRED_TMP))
            #
            G_line = deepcopy(T_l2).move_to(Ang_line.get_last_point(), aligned_edge=DOWN)
            #
            self.play(FadeIn(G_line, target_position=T_l2))
            self.wait()
            #
            cdot = Dot(T_l2.get_last_point()).set_color(SIN_G)
            sin_dot = Dot(G_line.get_last_point()).set_color(SIN_G)
            dot_line = DashedLine(start=cdot.get_center(), end=sin_dot.get_center()).set_color(GRAY_G)
            cdot = Dot(T_l2.get_last_point()).set_color(SIN_G).set_z_index(1)
            #
            self.play(Create(cdot))
            self.play(Create(dot_line))
            self.play(Create(sin_dot))
            self.wait()
            #
            arc.add_updater(lambda mob: mob.become(Arc(radius=1, start_angle=0, angle=ang.get_value(), arc_center=circ.get_center()).set_stroke(width=5.5).set_color(RED_G)))
            cdot.add_updater(lambda mob: mob.move_to(arc.get_last_point()))
            T_l1.add_updater(lambda mob: mob.put_start_and_end_on(start=circ.get_center(), end=circ.get_center()+[np.cos(ang.get_value()), 0, 0]).set_color(COS_G))
            T_l2.add_updater(lambda mob: mob.put_start_and_end_on(start=T_l1.get_last_point(), end=T_l1.get_last_point()+[0, np.sin(ang.get_value()), 0]).set_color(SIN_G))
            G_line.add_updater(lambda mob: mob.put_start_and_end_on(start=Ang_line.get_last_point(), end=Ang_line.get_last_point()+[0, np.sin(ang.get_value()), 0]).set_color(SIN_G))
            sin_dot.add_updater(lambda mob: mob.move_to(G_line.get_last_point()).set_z_index(0.5))
            dot_line.add_updater(lambda mob: mob.put_start_and_end_on(start=T_l3.get_last_point(), end=G_line.get_last_point()).set_color(GRAY_G))
            sin_curve = ParametricFunction(function=lambda t: ax_sin.c2p(t, np.sin(t)), t_range=[0, 2*PI]).set_color(SIN_G)
            sin_txt = TexGen(r'\sin(\alpha)', isMath=True, col=SIN_G).move_to([4, 0.5, 0])
            cos_txt = TexGen(r'\cos(\alpha)', isMath=True, col=COS_G).move_to([4, 3.5, 0])
            #
            self.play(Rotate(T_l3, angle=PI/8, about_point=circ.get_center()), ang.animate.set_value(PI/4+PI/8), rate_func=linear, run_time=1)
            self.wait()
            self.play(Rotate(T_l3, angle=-PI/4, about_point=circ.get_center()), ang.animate.set_value(PI/4+PI/8-PI/4), rate_func=linear, run_time=1.4)
            self.wait()
            self.play(Rotate(T_l3, angle=-PI/8+0.0001, about_point=circ.get_center()), ang.animate.set_value(0.0001), rate_func=linear, run_time=1)
            self.wait()
            Ang_line.clear_updaters()
            Ang_line.add_updater(lambda mob: mob.put_start_and_end_on(start=ax_sin.get_origin(), end=ax_sin.get_origin()+[ang.get_value(), 0, 0]).set_stroke(width=5.5).set_color(RRED_G))
            self.play(Rotate(T_l3, angle=2*PI-0.0001, about_point=circ.get_center()), ang.animate.set_value(2*PI-0.0001), Create(sin_curve), rate_func=linear, run_time=3)
            self.wait()
            self.play(Rotate(T_l3, angle=-(2*PI-0.0001), about_point=circ.get_center()), ang.animate.set_value(0.0001), rate_func=linear, run_time=3)
            self.play(DrawTxt(sin_txt))
            self.wait()
            #
            self.wait()
            ax_cos = deepcopy(ax_sin)
            self.add(ax_cos)
            #
            self.play(FadeOut(sin_dot, dot_line, Ang_line))
            self.play(ax_cos.animate.rotate(-PI/2, about_point=circ.get_center()))
            cos_xticks = ax_cos.get_x_axis().get_tick_marks()
            cos_yticks = ax_cos.get_y_axis().get_tick_marks()
            one_pi_cos = deepcopy(one_pi).next_to(cos_xticks[3], buff=0.1)
            two_pi_cos = deepcopy(two_pi).next_to(cos_xticks[-1], buff=0.1)
            one_cos = deepcopy(one).next_to(cos_yticks[1], UP, buff=0.1)
            mone_cos = deepcopy(mone).next_to(cos_yticks[0], UP, buff=0.1)
            self.play(DrawTxt(one_pi_cos), DrawTxt(two_pi_cos), DrawTxt(one_cos), DrawTxt(mone_cos))
            self.wait()
            #
            G_line.clear_updaters()
            sin_dot.clear_updaters()
            Ang_line.clear_updaters()
            Ang_line.add_updater(lambda mob: mob.put_start_and_end_on(start=ax_cos.get_origin(), end=ax_cos.get_origin()+[0, -ang.get_value(), 0]).set_stroke(width=5.5).set_color(RRED_G))
            A_line = Line(start=ax_cos.get_origin(), end=ax_cos.get_origin()+[np.cos(ang.get_value()), 0, 0]).set_stroke(width=5).set_color(COS_G)
            cos_dot = Dot(ax_cos.get_origin()+[np.cos(ang.get_value()), 0, 0]).set_color(COS_G)
            dot_line.clear_updaters()
            dot_line.add_updater(lambda mob: mob.put_start_and_end_on(start=T_l3.get_last_point(), end=A_line.get_last_point()).set_color(GRAY_G))
            #
            self.play(cdot.animate.set_color(COS_G), FadeIn(Ang_line))
            self.play(FadeIn(A_line, target_position=T_l1.get_center()))
            self.play(Create(dot_line))
            self.play(Create(cos_dot))
            self.wait()
            #
            A_line.add_updater(lambda mob: mob.put_start_and_end_on(start=Ang_line.get_last_point(), end=Ang_line.get_last_point()+[np.cos(ang.get_value()), 0, 0]).set_color(COS_G))
            cos_dot.add_updater(lambda mob: mob.move_to(A_line.get_last_point()).set_z_index(0.5))
            cos_curve = ParametricFunction(function=lambda t: ax_cos.c2p(t, np.cos(t)), t_range=[0, 2*PI]).set_color(COS_G)
            #
            self.play(Rotate(T_l3, angle=2*PI-0.0001, about_point=circ.get_center()), ang.animate.set_value(2*PI-0.0001), Create(cos_curve), rate_func=linear, run_time=3)
            self.play(Rotate(T_l3, angle=-(2*PI-0.0001), about_point=circ.get_center()), ang.animate.set_value(0.0001), rate_func=linear, run_time=3)
            self.wait()
            self.play(FadeOut(dot_line, cos_dot, A_line, one_cos, mone_cos, one_pi_cos, two_pi_cos))
            self.play(ax_cos.animate.rotate(PI/2, about_point=circ.get_center()), cos_curve.animate.rotate(PI/2, about_point=circ.get_center()))
            self.play(FadeOut(ax_cos))
            self.play(DrawTxt(cos_txt))
            self.wait()
            #
            ax_new = Axes(
                x_range=[-1.6*PI, 2.8*PI, PI/4],
                y_range=[-1.6, 1.5, 1],
                x_length=1.6*PI+2.8*PI,
                y_length=3,
                tips=True,
                axis_config={'tip_shape': StealthTip, 'include_ticks': True, 'tip_height': 0.2}
            ).move_to([0, -1.05, 0])
            ax_xticks = ax_new.get_x_axis().get_tick_marks()
            ax_yticks = ax_new.get_y_axis().get_tick_marks()
            m_pi = TexGen(r'-\pi', isMath=True, font_sz=35).next_to(ax_xticks[2], DOWN, buff=0.1)
            circ_stuff = VGroup(circ, cdot, T_l1, T_l2, T_l3, arc)
            Ang_line.clear_updaters()
            T_l1.clear_updaters()
            cdot.clear_updaters()
            #
            self.play(cos_curve.animate.shift(PI/2*RIGHT), run_time=1)
            self.wait()
            self.play(cos_curve.animate.shift(-PI/2*RIGHT), run_time=1)
            self.play(cdot.animate.set_color(WHITE_G))
            self.wait()
            self.play(FadeOut(sin_curve, sin_txt, cos_txt, cos_curve))
            self.play(ax_sin.animate.become(ax_new), circ_stuff.animate.move_to([-2.9, 2, 0]),
                      one.animate.next_to(ax_yticks[1], LEFT, buff=0.1), mone.animate.next_to(ax_yticks[0], LEFT, buff=0.1), one_pi.animate.next_to(ax_xticks[9], DOWN, buff=0.1), two_pi.animate.next_to(ax_xticks[13], DOWN, buff=0.1), FadeIn(m_pi, run_time=2))
            self.wait()
            #
            T_l2.clear_updaters()
            T_l3.clear_updaters()
            cfdot = Dot(circ.get_center()+[1, 0, 0])
            self.remove(cdot)
            self.add(cfdot)
            self.play(cfdot.animate.set_color(SIN_G))
            self.remove(T_l2)
            Ang_line.add_updater(lambda mob: mob.put_start_and_end_on(start=ax_new.get_origin(), end=ax_new.get_origin()+[ang.get_value(), 0, 0]).set_stroke(width=5.5).set_color(RRED_G))
            G_line_ax = Line(start=Ang_line.get_last_point(), end=Ang_line.get_last_point()+[0, np.sin(ang.get_value()), 0]).set_stroke(width=5).set_color(SIN_G)
            G_line_ax.add_updater(lambda mob: mob.put_start_and_end_on(start=Ang_line.get_last_point(), end=Ang_line.get_last_point()+[0, np.sin(ang.get_value()), 0]).set_stroke(width=5).set_color(SIN_G))
            G_line_c = deepcopy(G_line_ax)
            G_line_c.add_updater(lambda mob: mob.put_start_and_end_on(start=Ang_line.get_last_point(), end=Ang_line.get_last_point()+[0, np.sin(ang.get_value()), 0]).set_stroke(width=5).set_color(SIN_G).shift(3*UP))
            dot_line_new = DashedLine(start=T_l3.get_last_point(), end=ax_new.get_origin()).set_color(GRAY_G).set_z_index(-1)
            sin_dot2 = Dot(ax_new.get_origin()).set_color(SIN_G)
            self.play(Create(dot_line_new))
            self.play(Create(sin_dot2))
            sin_dot2.add_updater(lambda mob: mob.move_to(G_line_ax.get_last_point()))
            dot_line_new.add_updater(lambda mob: mob.put_start_and_end_on(start=G_line_ax.get_last_point(), end=G_line_ax.get_last_point()+[0, 3, 0]).set_color(GRAY_G).set_z_index(-1))
            T_l1.add_updater(lambda mob: mob.put_start_and_end_on(start=G_line_ax.get_start(), end=G_line_ax.get_start()-[np.cos(ang.get_value()), 0, 0]).set_color(COS_G).shift(3*UP))
            T_l3.add_updater(lambda mob: mob.put_start_and_end_on(start=T_l1.get_last_point(), end=T_l1.get_last_point()+[np.cos(ang.get_value()), np.sin(ang.get_value()), 0]))
            circ.add_updater(lambda mob: mob.move_to(G_line_ax.get_start()-[np.cos(ang.get_value()), 0, 0]).shift(3*UP))
            sin_curve2 = ParametricFunction(function=lambda t: ax_new.c2p(t, np.sin(t)), t_range=[0, 2.52*PI]).set_color(SIN_G)
            #
            self.add(G_line_ax, G_line_c, circ, arc, sin_dot2, dot_line_new)
            cfdot.clear_updaters()
            cfdot2 = Dot(circ.get_center()+[1, 0, 0]).set_color(SIN_G)
            cfdot2.add_updater(lambda mob: mob.move_to(Ang_line.get_last_point()+[0, 3+np.sin(ang.get_value()), 0]).set_color(SIN_G))
            self.remove(cfdot)
            self.add(cfdot2)
            self.play(ang.animate.set_value(2.52*PI), Create(sin_curve2), rate_func=linear, run_time=2.52*PI*0.6)
            T_l1.clear_updaters()
            T_l1.add_updater(lambda mob: mob.put_start_and_end_on(start=G_line_ax.get_start(), end=G_line_ax.get_start()-[np.cos(ang.get_value()), 0, 0]).set_color(COS_G).shift(3*UP))
            self.play(ang.animate.set_value(0.0001), rate_func=linear, run_time=2.52*PI*0.6)
            msin_curve2 = ParametricFunction(function=lambda t: ax_new.c2p(t, np.sin(t)), t_range=[0, 4.45]).set_color(SIN_G).rotate(PI, about_point=ax_new.get_origin())
            T_l1.clear_updaters()
            T_l1.add_updater(lambda mob: mob.put_start_and_end_on(start=G_line_ax.get_start(), end=G_line_ax.get_start()-[np.cos(ang.get_value()), 0, 0]).set_color(COS_G).shift(3*UP))
            self.play(ang.animate.set_value(-4.45+0.0001), Create(msin_curve2), rate_func=linear, run_time=(4.45)*0.6)
            T_l1.clear_updaters()
            T_l1.add_updater(lambda mob: mob.put_start_and_end_on(start=G_line_ax.get_start(), end=G_line_ax.get_start()-[np.cos(ang.get_value()), 0, 0]).set_color(COS_G).shift(3*UP))
            T_l3.clear_updaters()
            T_l3.add_updater(lambda mob: mob.put_start_and_end_on(start=T_l1.get_last_point(), end=T_l1.get_last_point()+[np.cos(ang.get_value()), np.sin(ang.get_value()), 0]))
            self.play(ang.animate.set_value(-0.0001), rate_func=linear, run_time=(4.45)*0.6)
            bug_line = Line(start=circ.get_center(), end=circ.get_center()+[1, 0, 0]).set_stroke(width=5).set_z_index(-1)
            self.add(bug_line)
            self.remove(T_l1, T_l3)
            T_l1.clear_updaters()
            T_l3.clear_updaters()
            self.wait()

        def play_wave2():
            Trig = Triangle().set_color(YELL_G).set_stroke(width=5).scale(2.7).rotate(2*PI/3, about_point=ORIGIN).move_to(ORIGIN)
            Trig.shift(-Trig.get_center_of_mass())
            #
            self.play(Create(Trig))
            self.wait()
            #
            ax_wave = Axes(
                x_range=[-2*PI-0.3, 2*PI+0.3, PI/4],
                y_range=[-1.5, 1.5, 1],
                x_length=2*(2*PI+0.3),
                y_length=3,
                tips=True,
                axis_config={'tip_shape': StealthTip, 'include_ticks': True, 'tip_height': 0.2}
            ).shift(0.6*DOWN)
            sin_xticks = ax_wave.get_x_axis().get_tick_marks()
            sin_yticks = ax_wave.get_y_axis().get_tick_marks()
            one_pi = TexGen(r'\pi', isMath=True, font_sz=35).next_to(sin_xticks[11], DOWN, buff=0.1)
            two_pi = TexGen(r'2\pi', isMath=True, font_sz=35).next_to(sin_xticks[15], DOWN, buff=0.1)
            mone_pi = TexGen(r'-\pi', isMath=True, font_sz=35).next_to(sin_xticks[4], DOWN, buff=0.1)
            mtwo_pi = TexGen(r'-2\pi', isMath=True, font_sz=35).next_to(sin_xticks[0], DOWN, buff=0.1)
            one = TexGen(r'1', isMath=True, font_sz=35).next_to(sin_yticks[1], LEFT, buff=0.1)
            mone = TexGen(r'-1', isMath=True, font_sz=35).next_to(sin_yticks[0], LEFT, buff=0.1)
            wave = ParametricFunction(function=lambda t: ax_wave.c2p(t, np.sin(t)), t_range=[-2*PI, 2*PI]).set_color(YELL_G)
            sin = TexGen(r'\sin(', isMath=True, col=YELL_G)
            alpha = TexGen(r'\alpha', isMath=True, col=YELL_G)
            klammer = TexGen(r')', isMath=True, col=YELL_G)
            g1 = VGroup(sin, alpha.next_to(sin, buff=0.07), klammer.next_to(alpha, buff=0.07)).move_to([0, 3, 0]).set_stroke(color=YELL_G)
            mdot = TexGen(r'\cdot', isMath=True, col=YELL_G).next_to(sin, LEFT, buff=0.15)
            #
            self.play(ReplacementTransform(Trig, wave), Create(ax_wave), DrawTxt(one_pi), DrawTxt(two_pi), DrawTxt(mone), DrawTxt(mone_pi), DrawTxt(mtwo_pi), DrawTxt(one))
            self.wait()
            self.play(DrawTxt(g1))
            self.wait()
            #
            A = ValueTracker(1)
            A_num = DecimalNumber(A.get_value(), 1, font_size=50, color=YELL_G)
            A_num.add_updater(lambda mob: mob.set_value(A.get_value()))
            o = ValueTracker(1)
            o_num = DecimalNumber(A.get_value(), 1, font_size=50, color=YELL_G)
            o_num.add_updater(lambda mob: mob.set_value(o.get_value()))
            mdot2 = TexGen(r'\cdot', isMath=True, col=YELL_G)
            plus = TexGen(r'+', isMath=True, col=YELL_G)
            plus2 = TexGen(r'+', isMath=True, col=YELL_G)
            a0 = ValueTracker(0)
            a0_num = DecimalNumber(a0.get_value(), 1, font_size=50, color=YELL_G)
            a0_num.add_updater(lambda mob: mob.set_value(a0.get_value()))
            D = ValueTracker(0)
            D_num = DecimalNumber(D.get_value(), 1, font_size=50, color=YELL_G)
            D_num.add_updater(lambda mob: mob.set_value(D.get_value()))
            wave.add_updater(lambda mob: mob.become(ParametricFunction(function=lambda t: ax_wave.c2p(t, A.get_value()*np.sin(o.get_value()*t+a0.get_value())+D.get_value()), t_range=[-2*PI, 2*PI]).set_color(YELL_G)))
            
            mdot.next_to(A_num, buff=0.15)
            sin2 = deepcopy(sin).next_to(mdot, buff=0.15).shift(0.03*DOWN)
            o_num.next_to(sin2, buff=0.15).shift(0.03*UP)
            mdot2.next_to(o_num, buff=0.15)
            alpha2 = deepcopy(alpha).next_to(mdot2, buff=0.15).shift(0.03*DOWN)
            plus.next_to(alpha2, buff=0.15).shift(0.03*UP)
            a0_num.next_to(plus, buff=0.15)
            klammer2 = deepcopy(klammer).next_to(a0_num, buff=0.15)
            plus2.next_to(klammer2, buff=0.15)
            D_num.next_to(plus2, buff=0.15)
            Group(A_num, mdot, sin2, o_num, mdot2, alpha2, plus, a0_num, klammer2, plus2, D_num).move_to([0, 3, 0])
            #
            self.play(ReplacementTransform(g1, VGroup(sin2, alpha2, klammer2)))
            self.play(DrawTxt(A_num), DrawTxt(o_num), DrawTxt(mdot), DrawTxt(plus), DrawTxt(mdot2), DrawTxt(plus2), DrawTxt(D_num), DrawTxt(a0_num))
            self.play(A.animate.set_value(3), rate_func=there_and_back, run_time=3)
            self.play(o.animate.set_value(3), rate_func=there_and_back, run_time=3)
            self.play(a0.animate.set_value(2), rate_func=there_and_back, run_time=3)
            self.play(D.animate.set_value(2), rate_func=there_and_back, run_time=3)
            self.wait()
            ealpha = TexGen(r'e^\frac{\alpha}{2}', isMath=True, col=YELL_G).move_to(alpha2).shift(0.1*UP)
            wave2 = ParametricFunction(function=lambda t: ax_wave.c2p(t, np.sin(np.exp(t/2))), t_range=[-2*PI, 2*PI]).set_color(YELL_G)

            self.play(Group(A_num, mdot, sin2, o_num, mdot2).animate.shift(0.1*LEFT), 
                      ReplacementTransform(wave, wave2), ReplacementTransform(alpha2, ealpha),
                      Group(plus, a0_num, klammer2, plus2, D_num).animate.shift(0.09*RIGHT))

        def thumbnail():
            Trig = Triangle().set_color(YELL_G).set_stroke(width=9).scale(2).rotate(2*PI/3, about_point=ORIGIN).move_to(ORIGIN).shift(4.5*LEFT)
            
            arr = TexGen(r'\rightarrow', isMath=True, font_sz=200).shift(1.3*LEFT)
            ax_wave = Axes(
                x_range=[0, 6*PI],
                y_range=[-1, 1],
                x_length=5.5,
                y_length=Trig.width,
                tips=True,
                axis_config={'tip_shape': StealthTip, 'include_ticks': True, 'tip_height': 0.2}
            )
            self.add(Trig, arr)
            self.add(ParametricFunction(function=lambda t: ax_wave.c2p(t, np.sin(t)), t_range=[0, 6*PI]).set_color(YELL_G).set_stroke(width=9).next_to(arr, buff=1))

        # GLOBAL VARs
        angry = ImageMobject('angry.png')
        angry.height = 1.5
        angry.shift(2.5*UP)
        coolmoji = ImageMobject('cool.png')
        coolmoji.height = 1.5

        # ANIMATE
        self.wait()
        play_intro()
        play_angle()
        play_triangle()
        play_trig()
        play_wave()
        play_wave2()
        thumbnail()
        self.wait()
