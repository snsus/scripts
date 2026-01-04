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

class Bulb():
    def __init__(self, on, position, bulb_tex):
        self.on = on
        self.off_state = ImageMobject(filename_or_array="off.png")
        self.on_state = ImageMobject(filename_or_array="on.png")
        self.off_state.move_to(position)
        self.on_state.move_to(position)
        self.position = position
        self.off_state.height = 1
        self.on_state.height = 1
        self.bulb_tex = bulb_tex
        self.bulb_tex_onscreen = False
        self.isPlus = True

    def isOn(self):
        return self.on
    
    def get_off_state(self):
        return self.off_state
    
    def get_on_state(self):
        return self.on_state
    
    def change_y(self, new_y):
        self.position[1] = new_y
        self.off_state.move_to(self.position)
        self.on_state.move_to(self.position)

    
class Scenery(MovingCameraScene):
    def construct(self):
        CAM = self.camera.frame

        # COLORS
        WHITE_G = color_gradient([WHITE, WHITE], 2)
        YEBLUE_G = color_gradient([ManimColor.from_hex("#FFED95"), ManimColor.from_hex("#16E3F9")], 200)
        RED_G = color_gradient([ManimColor.from_hex("#FF5555"), ManimColor.from_hex("#FF073A")], 200)
        GRAY_G = color_gradient([ManimColor.from_hex("#B1B1B1"), ManimColor.from_hex("#B1B1B1")], 200)
        DGRAY_G = color_gradient([ManimColor.from_hex("#7E7E7E"), ManimColor.from_hex("#7E7E7E")], 200)
        PIX_green = ManimColor.from_hex("#03AC47")
        PIX_blue = ManimColor.from_hex("#59D3F1")
        PIX_yell = ManimColor.from_hex("#B3D218")
        YELL = ManimColor.from_hex("#FFD600")
        PRED = ManimColor.from_hex("#FF0000")
        PGREEN = ManimColor.from_hex("#00BF00")
        PBLUE = ManimColor.from_hex("#0000FF")
        TRN_col_up = ManimColor.from_hex("#CACBCA")
        TRN_col_down = ManimColor.from_hex("#82AEC0")

        def toggle(nums, sign=False, run_t=0.4):
            anims = []
            if nums:
                bulbs_to_turn_on = []
                bulbs_to_turn_off = []
                for b in [bulbs[i] for i in nums]:
                    if b.isOn():
                        bulbs_to_turn_off.append(b)
                    else:
                        bulbs_to_turn_on.append(b)
                    b.on = not b.on
                if bulbs_to_turn_off:
                    anims.append(FadeOut(*(B.get_on_state() for B in bulbs_to_turn_off), run_time=0.1))
                    anims.append(B.bulb_tex.animate.set_color(GRAY_G) for B in bulbs_to_turn_off if B.bulb_tex_onscreen)
                if bulbs_to_turn_on:
                    anims.append((Flash(point=B.get_off_state(), flash_radius=0.3, run_time=run_t) for B in bulbs_to_turn_on))
                    anims.append(FadeIn(*(B.get_on_state() for B in bulbs_to_turn_on), run_time=run_t))
                    anims.append(B.bulb_tex.animate.set_color(YELL) for B in bulbs_to_turn_on if B.bulb_tex_onscreen)
            if sign:
                nonlocal plus, minus;
                if b9.isPlus:
                    anims.append(Flash(point=b9.get_off_state(), flash_radius=0.3, run_time=run_t))
                    anims.append(FadeIn(b9.get_on_state(), run_time=run_t))
                    anims.append(ReplacementTransform(plus, minus))
                    plus = TexGen(r'+', isMath=True, font_sz=50, col=YEBLUE_G).move_to(pot9.get_center())
                else:
                    anims.append(FadeOut(b9.get_on_state(), run_time=0.1))
                    anims.append(ReplacementTransform(minus, plus))
                    minus = TexGen(r'-', isMath=True, font_sz=50, col=YEBLUE_G).move_to(pot9.get_center())
                b9.isPlus = not b9.isPlus

            self.play(*(anims), run_time=run_t)
        
        def TexGen(string, font_sz=50, col=WHITE_G, isMath=False):
            if not isMath:
                return Tex(fr'{string}', font_size=font_sz).set_color(col).set_stroke(color=average_color(col[0], col[-1]), width=1)
            else:
                return MathTex(fr'{string}', font_size=font_sz).set_color(col).set_stroke(color=average_color(col[0], col[-1]), width=1)
            
        def DrawTxt(txt):
            return DrawBorderThenFill(txt, stroke_color=txt.get_stroke_colors(), run_time=1)
        
        def BounceIn(mobjects) -> Animation:
            bounce_anims = []
            for mob in mobjects:
                bounce_anims.append(GrowFromCenter(mob, rate_func=rate_functions.ease_out_back, run_time=0.5))
            return bounce_anims
        
        def BubbleNum(bubble_num, col=YEBLUE_G, scale=0.7):
            nonlocal current_bubble_num; 
            new_bubble_num = TexGen(fr'{bubble_num}', isMath=True, font_sz=100, col=col).scale_to_fit_height(scale).move_to(speech.get_center()).shift(0.1*UP)
            self.play(ReplacementTransform(current_bubble_num, new_bubble_num, run_time=0.5))
            current_bubble_num = new_bubble_num
        
        def ChangeDots(dot_list, col) -> Animation:
            anims = []
            for d in dot_list:
                anims.append(d.animate.set_color(col).set_stroke(color=col))
            return anims
        
        def play_intro():     
            self.play(BounceIn([b.get_off_state() for b in bulbs])) 
            self.wait()
            toggle([0])
            self.wait()
            toggle([0])
            self.wait()
            self.play(DrawTxt(g_damitzd))
            self.wait()
            self.play(t_zahlen.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1))
            self.wait()
            self.play(FadeIn(t_N_small, target_position=t_zahlen.get_center()))
            self.play(DrawTxt(t_N_nums))
            self.wait()
            self.play(FadeIn(t_Z_small, target_position=t_zahlen.get_center()))
            self.play(DrawTxt(t_Z_nums))
            self.wait()
            self.play(FadeIn(t_Q_small, target_position=t_zahlen.get_center()))
            self.play(DrawTxt(t_Q_nums))
            self.wait()
            self.play(FadeIn(t_R_small, target_position=t_zahlen.get_center()))
            self.play(DrawTxt(t_R_nums))
            self.play(FadeIn(t_C_small, target_position=t_zahlen.get_center()))
            self.play(DrawTxt(t_C_nums))
            self.wait()
            self.play(FadeOut(*(b.get_off_state() for b in bulbs)), FadeOut(g_damitzd, intro_nums))
            self.play(FadeIn(gif1))
            self.play(FadeIn(gif2))
            self.play(FadeIn(gif3))
            self.play(FadeIn(gif4))
            self.wait()
            self.play(FadeIn(paper))
            self.wait(11)
            self.play(FadeOut(gif1, gif2, gif3, gif4, paper))
            self.wait()

        def play_N():
            nonlocal current_bubble_num;
            for b in bulbs:
                b.change_y(1.5)
            self.play(DrawTxt(t_N_big))
            self.play(t_N_big.animate.move_to([-6, -3, 0]).scale(0.4))
            self.play(BounceIn([b.get_off_state() for b in bulbs]))
            self.wait()
            self.play(DrawTxt(t_anzahl))
            self.wait()
            self.play(BounceIn(person))
            self.wait()
            toggle([3, 5, 8])
            self.play(BounceIn(speech))
            self.play(DrawTxt(current_bubble_num))
            self.wait()
            toggle([0, 1, 2, 4, 6, 7, 9])
            BubbleNum(10)
            self.wait()
            toggle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
            BubbleNum(0)
            self.play(t_N_big.animate.become(t_N0_big))
            self.play(FadeOut(t_anzahl))
            self.wait()
            self.play(DrawTxt(NL_0_10_from), DrawTxt(NL_0_10_to), Create(NL_0_10))
            self.play(*[Create(d) for d in DOTS_0_10])
            self.wait()
            self.play(ChangeDots(DOTS_0_10[1:10], RED_G))
            self.wait()
            toggle([0, 1])
            BubbleNum(2)
            self.wait()
            toggle([0, 1, 6, 9])
            self.play(current_bubble_num.animate.set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1])))
            self.wait()    
            toggle([6, 9])
            self.wait()
            self.play(FadeOut(speech, current_bubble_num, NL_0_10, *DOTS_0_10, NL_0_10_from, NL_0_10_to))
            self.wait(2)
            self.play(FadeIn(b0.bulb_tex, target_position=[4.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b1.bulb_tex, target_position=[3.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b2.bulb_tex, target_position=[2.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b3.bulb_tex, target_position=[1.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b4.bulb_tex, target_position=[0.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b5.bulb_tex, target_position=[-0.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b6.bulb_tex, target_position=[-1.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b7.bulb_tex, target_position=[-2.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b8.bulb_tex, target_position=[-3.5, 4, 0]), run_time=0.1)
            self.play(FadeIn(b9.bulb_tex, target_position=[-4.5, 4, 0]), run_time=0.1)
            for b in bulbs:
                b.bulb_tex_onscreen = True
            self.wait()
            self.play(DrawTxt(t_stelle))
            self.wait(2)
            toggle([2])
            self.play(BounceIn(speech))
            current_bubble_num = TexGen(r'3', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            self.play(DrawTxt(current_bubble_num))
            self.wait()
            toggle([2])
            BubbleNum(0)
            self.wait()
            self.play(FadeOut(t_stelle))
            self.play(DrawTxt(NL_0_10_from), DrawTxt(NL_0_10_to), Create(NL_0_10))
            self.play(*[Create(d) for d in DOTS_0_10])
            self.play(ChangeDots(DOTS_0_10[1:10], YEBLUE_G))
            self.wait()
            self.play(FadeOut(NL_0_10, *DOTS_0_10, NL_0_10_from, NL_0_10_to, speech, current_bubble_num))
            self.wait(2)
            self.play(FadeIn(*(plus_signs)))      
            toggle([7, 3])
            self.play(BounceIn(speech))
            current_bubble_num = TexGen(r'12', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            self.play(DrawTxt(current_bubble_num))
            toggle([8, 6, 4, 0, 1, 2, 9, 5])
            BubbleNum(55)
            toggle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
            BubbleNum(0)
            self.play(DrawTxt(NL_0_55_from), DrawTxt(NL_0_55_to), Create(NL_0_55))
            self.play(*[Create(d) for d in DOTS_0_55])
            self.play(ChangeDots(DOTS_0_55[3:55], RED_G))
            self.wait()
            self.play(FadeOut(NL_0_55, *DOTS_0_55, NL_0_55_from, NL_0_55_to, speech, person, *(plus_signs), t_N_big, *(b.bulb_tex for b in bulbs), current_bubble_num))
            for b in bulbs:
                b.bulb_tex_onscreen = False

        def play_WV(alone=False):
            if alone:
                for b in bulbs:
                    b.change_y(1.5)
                self.add(*(b.get_off_state() for b in bulbs)) 
            self.wait()
            self.play(DrawTxt(t_wv.shift(3*UP)))
            self.wait()
            self.play(FadeOut(*(bulbs[i].get_off_state() for i in range(8))))
            self.wait()
            self.play(b9.get_off_state().animate.move_to([-5, 1, 0]), b8.get_off_state().animate.move_to([-4, 1, 0]))
            self.play(BounceIn(brace_paar_1), DrawTxt(t_paar_1))
            self.wait()
            self.play(FadeIn(paar_2, target_position=paar_1.get_center()))
            self.play(BounceIn(brace_paar_2), DrawTxt(t_paar_2))
            self.wait()
            self.play(FadeIn(paar_3, target_position=paar_1.get_center()))
            self.play(BounceIn(brace_paar_3), DrawTxt(t_paar_3))
            self.wait()
            self.play(FadeIn(paar_4, target_position=paar_1.get_center()))
            self.play(BounceIn(brace_paar_4), DrawTxt(t_paar_4))
            self.wait()
            self.play(FadeOut(brace_paar_1, brace_paar_2, brace_paar_3, brace_paar_4, t_paar_1, t_paar_2, t_paar_3, t_paar_4))
            self.wait()
            self.play(BounceIn(brace_paare), DrawTxt(t_paare))
            self.wait()
            self.play(FadeOut(brace_paare, t_paare, paar_2, paar_3, paar_4))
            self.play(DrawTxt(t_mogl1), DrawTxt(t_mogl2))
            self.wait()
            self.play(DrawTxt(t_mogl_cdot1), DrawTxt(t_mogl_ges))
            self.wait()
            self.play(BounceIn(b7.get_off_state().move_to([-3, 1, 0])))
            self.play(FadeOut(t_mogl_ges))
            self.wait()
            t_mogl_eq.shift(RIGHT)
            t_mogl_8.next_to(t_mogl_eq, RIGHT)
            t_mogl3.next_to(b7.get_off_state(), DOWN)
            self.play(DrawTxt(t_mogl3))
            self.wait()
            self.play(DrawTxt(t_mogl_cdot2), DrawTxt(t_mogl_eq), DrawTxt(t_mogl_8))
            self.wait()
            self.play(DrawTxt(t_mogl_ges_8))
            self.play(FadeOut(t_mogl1, t_mogl2, t_mogl_cdot1, t_mogl3, t_mogl_cdot2, t_mogl_eq, t_mogl_8, t_mogl_ges_8))
            self.wait()
            self.play(b9.get_off_state().animate.move_to([-4.5, 1.5, 0]), b8.get_off_state().animate.move_to([-3.5, 1.5, 0]), b7.get_off_state().animate.move_to([-2.5, 1.5, 0]))
            self.play(BounceIn([b.get_off_state() for b in bulbs[:7]]))
            self.play(BounceIn(brace_10bulbs.shift(DOWN)), DrawTxt(t_10Bulbs_mogl.shift(DOWN)))
            self.wait()
            self.play(FadeOut(brace_10bulbs, t_10Bulbs_mogl, t_wv))
            self.wait()

        def play_N_next(alone=False):
            if alone:
                for b in bulbs:
                    b.change_y(1.5)
                self.add(*(b.get_off_state() for b in bulbs))
                for d in DOTS_0_55[3:55]:
                    d.set_color(RED_G).set_stroke(color=RED_G)
            nonlocal current_bubble_num;
            self.play(FadeIn(NL_0_55, *DOTS_0_55, NL_0_55_from, NL_0_55_to, t_N0_big, *(plus_signs), *(b.bulb_tex for b in bulbs)))
            for b in bulbs:
                b.bulb_tex_onscreen = True
            self.wait()
            self.play(DOTS_0_55[0].animate.shift(dot_move*UP))
            self.wait()
            self.play(DOTS_0_55[0].animate.shift(dot_move*DOWN), DOTS_0_55[1].animate.shift(dot_move*UP))
            self.wait()
            toggle([0])
            self.wait()
            self.play(DOTS_0_55[1].animate.shift(dot_move*DOWN), DOTS_0_55[2].animate.shift(dot_move*UP))
            self.wait()
            toggle([0, 1])
            self.wait()
            self.play(DOTS_0_55[2].animate.shift(dot_move*DOWN), DOTS_0_55[3].animate.shift(dot_move*UP))
            self.wait()
            toggle([1, 2])
            self.wait()
            toggle([0, 1, 2])
            self.wait()
            self.play(DrawTxt(rect_around_bulbtex))
            self.wait()
            self.play(FadeOut(b2.bulb_tex))
            b2.bulb_tex = TexGen(r'4', isMath=True, font_sz=40, col=GRAY_G).move_to([2.5, 2.5, 0])
            self.wait()
            self.play(DrawTxt(b2.bulb_tex))
            self.wait()
            self.play(ChangeDots(DOTS_0_55[3], YEBLUE_G))
            self.wait()
            toggle([2, 3, 4, 5, 6, 7, 8, 9])
            self.wait()
            self.play(Create(DOT_56), Transform(NL_0_55_to, NL_0_55_to56))
            self.wait()
            self.play(DOTS_0_55[3].animate.shift(dot_move*DOWN), DOT_56.animate.shift(dot_move*DOWN))
            toggle([2, 3, 4, 5, 6, 7, 8, 9])
            self.wait()
            self.play(FadeOut(NL_0_55, *DOTS_0_55, DOT_56, NL_0_55_from, NL_0_55_to))
            self.wait()
            self.play(rect_around_bulbtex.animate.move_to(b3.bulb_tex.get_center()))
            self.wait()
            self.play(FadeOut(b3.bulb_tex))
            self.wait()
            toggle([0, 1, 2])
            self.wait()
            toggle([0])
            self.wait()
            toggle([0, 1])
            self.wait()
            toggle([0])
            self.wait()
            b3.bulb_tex = TexGen(r'8', isMath=True, font_sz=40, col=GRAY_G).move_to([1.5, 2.5, 0])
            self.play(DrawTxt(b3.bulb_tex))
            self.wait()
            for i in range(3):
                self.play(Create(curv_arrows[i], run_time=0.5), BounceIn(t_doubles[i]))
            self.wait()
            self.play(FadeOut(rect_around_bulbtex, *(b.bulb_tex for b in bulbs[4:])))
            toggle([0, 1, 2])
            self.wait()
            b4.bulb_tex = TexGen(r'16', isMath=True, font_sz=40, col=GRAY_G).move_to([0.5, 2.5, 0])
            b5.bulb_tex = TexGen(r'32', isMath=True, font_sz=40, col=GRAY_G).move_to([-0.5, 2.5, 0])
            b6.bulb_tex = TexGen(r'64', isMath=True, font_sz=40, col=GRAY_G).move_to([-1.5, 2.5, 0])
            b7.bulb_tex = TexGen(r'128', isMath=True, font_sz=40, col=GRAY_G).move_to([-2.5, 2.5, 0])
            b8.bulb_tex = TexGen(r'256', isMath=True, font_sz=40, col=GRAY_G).move_to([-3.5, 2.5, 0])
            b9.bulb_tex = TexGen(r'512', isMath=True, font_sz=40, col=GRAY_G).move_to([-4.5, 2.5, 0])
            for i in range(4, 10):
                self.play(Create(curv_arrows[i-1]), DrawTxt(bulbs[i].bulb_tex), BounceIn(t_doubles[i-1]), run_time=0.3)
            self.wait(2)
            self.play(ReplacementTransform(b0.bulb_tex, pot0), ReplacementTransform(b1.bulb_tex, pot1), ReplacementTransform(b2.bulb_tex, pot2), ReplacementTransform(b3.bulb_tex, pot3), ReplacementTransform(b4.bulb_tex, pot4), ReplacementTransform(b5.bulb_tex, pot5), ReplacementTransform(b6.bulb_tex, pot6), ReplacementTransform(b7.bulb_tex, pot7), ReplacementTransform(b8.bulb_tex, pot8), ReplacementTransform(b9.bulb_tex, pot9), run_time=1)
            b0.bulb_tex = pot0
            b1.bulb_tex = pot1
            b2.bulb_tex = pot2
            b3.bulb_tex = pot3
            b4.bulb_tex = pot4
            b5.bulb_tex = pot5
            b6.bulb_tex = pot6
            b7.bulb_tex = pot7
            b8.bulb_tex = pot8
            b9.bulb_tex = pot9
            self.wait()
            self.play(FadeOut(*curv_arrows, *t_doubles))
            self.wait()
            self.play(FadeIn(orient0, target_position=b0.bulb_tex.get_center()), FadeIn(orient1, target_position=b1.bulb_tex.get_center()), FadeIn(orient2, target_position=b2.bulb_tex.get_center()), FadeIn(orient3, target_position=b3.bulb_tex.get_center()), FadeIn(orient4, target_position=b4.bulb_tex.get_center()), FadeIn(orient5, target_position=b5.bulb_tex.get_center()), FadeIn(orient6, target_position=b6.bulb_tex.get_center()), FadeIn(orient7, target_position=b7.bulb_tex.get_center()), FadeIn(orient8, target_position=b8.bulb_tex.get_center()), FadeIn(orient9, target_position=b9.bulb_tex.get_center()))
            current_bubble_num = TexGen(r'73', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            self.wait()
            self.play(BounceIn(person))
            self.wait()
            toggle([0, 3, 6])
            self.play(BounceIn(speech))
            self.play(DrawTxt(current_bubble_num))
            self.wait()
            toggle([0, 3, 6])
            self.wait()
            BubbleNum(r'42?')
            self.wait()
            toggle([5])
            BubbleNum(32)
            self.wait()
            toggle([3])
            BubbleNum(40)
            self.wait()
            toggle([1])
            BubbleNum(42)
            self.wait()
            toggle([0, 2, 4, 6, 7, 8, 9])
            BubbleNum(1023)
            self.wait()
            toggle([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
            BubbleNum(0)
            self.wait()
            self.play(FadeOut(*orients, current_bubble_num, speech, person))
            self.wait()
            CAM.save_state()
            self.play(DrawTxt(NL_0_1023_from), DrawTxt(NL_0_1023_to), Create(NL_0_1023), *[Create(d) for d in DOTS_0_1023])
            self.wait()
            self.play(CAM.animate.move_to(NL_0_1023.n2p(20)).scale(0.04), NL_0_1023.animate.set_stroke(width=0.01), FadeIn(NL_0_1023_small), run_time=1)
            self.wait(1)
            self.play(CAM.animate.move_to(NL_0_1023.n2p(1003)), rate_func=rate_functions.ease_in_out_expo, run_time=4)
            self.wait(1)
            self.play(Restore(CAM), FadeOut(NL_0_1023_small), NL_0_1023.animate.set_stroke(width=2))
            self.play(FadeOut(t_N0_big, *(b.bulb_tex for b in bulbs), *plus_signs, *(b.get_off_state() for b in bulbs), NL_0_1023, NL_0_1023_from, NL_0_1023_to, *DOTS_0_1023))
        
        def play_Z(alone=False):
            if alone:
                for b in bulbs:
                    b.change_y(1.5)
                b0.bulb_tex = pot0
                b1.bulb_tex = pot1
                b2.bulb_tex = pot2
                b3.bulb_tex = pot3
                b4.bulb_tex = pot4
                b5.bulb_tex = pot5
                b6.bulb_tex = pot6
                b7.bulb_tex = pot7
                b8.bulb_tex = pot8
                b9.bulb_tex = pot9
            nonlocal current_bubble_num;
            self.play(DrawTxt(t_Z_big))
            self.play(t_Z_big.animate.move_to([-6, -3, 0]).scale(0.4))
            self.play(BounceIn([b.get_off_state() for b in bulbs]))
            self.play(FadeIn(*(b.bulb_tex for b in bulbs), *plus_signs))
            self.wait()
            self.play(DrawTxt(festes_minus))
            self.wait()
            self.play(BounceIn(person))
            self.wait()
            current_bubble_num = TexGen(r'-3', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            toggle([0, 1])
            self.play(BounceIn(speech))
            self.play(DrawTxt(current_bubble_num))
            self.wait()
            self.play(DrawTxt(NL_minus1023_from), DrawTxt(NL_minus1023_to), Create(NL_minus1023))
            self.play(FadeOut(NL_minus1023, NL_minus1023_from, NL_minus1023_to, festes_minus, speech, current_bubble_num))
            toggle([0, 1])
            self.wait()
            self.play(DrawTxt(rect_around_bulbtex.move_to(b9.bulb_tex.get_center())))
            self.wait()
            self.play(ReplacementTransform(b9.bulb_tex, plus), FadeOut(plus_signs[-1]))
            current_bubble_num = TexGen(r'19', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            self.wait()
            toggle([], sign=True)
            self.wait()
            toggle([], sign=True)
            self.play(FadeOut(rect_around_bulbtex))
            self.wait()
            toggle([5, 0])
            self.play(BounceIn(speech))
            self.play(DrawTxt(current_bubble_num))
            self.wait()
            toggle([], sign=True)
            BubbleNum(r'-19')
            CAM.save_state()
            self.wait()
            self.play(DrawTxt(NL_minus511_from), DrawTxt(NL_minus511_to), Create(NL_minus511), *[Create(d) for d in DOTS_minus511])
            self.wait()
            self.play(CAM.animate.move_to(NL_minus511.n2p(-491)).scale(0.04), NL_minus511.animate.set_stroke(width=0.01), FadeIn(NL_minus511_small), run_time=1)
            self.wait(1)
            self.play(CAM.animate.move_to(NL_minus511.n2p(0)), rate_func=rate_functions.ease_in_out_expo, run_time=4)
            self.wait(1)
            self.play(DOTS_minus511[511].animate.shift(dot_move*UP*0.04))
            self.play(DrawBorderThenFill(plus_null, stroke_color=plus_null.get_stroke_colors(), stroke_width=0.1, run_time=1), 
                      DrawBorderThenFill(minus_null, stroke_color=minus_null.get_stroke_colors(), stroke_width=0.1, run_time=1))
            self.wait()
            self.play(plus_null.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      minus_null.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      ReplacementTransform(DOTS_minus511[511], g_null_dots))
            self.wait()
            self.play(DrawBorderThenFill(lim, stroke_color=lim.get_stroke_colors(), stroke_width=0.1, run_time=1))
            minus_null.save_state()
            plus_null.save_state()
            self.wait()
            self.play(minus_null.animate.shift(0.1624*DOWN+0.036*RIGHT).scale(0.7))
            self.play(DrawBorderThenFill(lim_minusinf, stroke_color=lim_minusinf.get_stroke_colors(), stroke_width=0.1, run_time=1))
            self.play(Restore(minus_null), plus_null.animate.shift(0.1624*DOWN+0.024*LEFT).scale(0.7), FadeOut(lim_minusinf, run_time=0.1))
            self.play(DrawBorderThenFill(lim_plusinf, stroke_color=lim_minusinf.get_stroke_colors(), stroke_width=0.1, run_time=1))
            self.play(Restore(plus_null), FadeOut(lim_plusinf))
            self.wait()
            self.play(Restore(CAM), FadeOut(NL_minus511_small, plus_null, minus_null, lim, *DOTS_minus511, g_null_dots), NL_minus511.animate.set_stroke(width=2))
            self.wait()
            toggle([0, 5], sign=True)
            self.play(FadeOut(plus, *(b.bulb_tex for b in bulbs), *plus_signs[0:8], *(b.get_off_state() for b in bulbs), current_bubble_num, speech, person, t_Z_big, NL_minus511, NL_minus511_from, NL_minus511_to))
           

        def play_Q(alone=False):
            if alone:
                for b in bulbs:
                    b.change_y(1.5)
                b0.bulb_tex = pot0
                b1.bulb_tex = pot1
                b2.bulb_tex = pot2
                b3.bulb_tex = pot3
                b4.bulb_tex = pot4
                b5.bulb_tex = pot5
                b6.bulb_tex = pot6
                b7.bulb_tex = pot7
                b8.bulb_tex = pot8
                b9.bulb_tex = plus            
            nonlocal current_bubble_num;
            self.play(DrawTxt(t_Q_big))
            self.play(t_Q_big.animate.move_to([-6, -3, 0]).scale(0.4))
            self.play(BounceIn([b.get_off_state() for b in bulbs]))
            self.play(FadeIn(*(b.bulb_tex for b in bulbs), *plus_signs[0:8]))
            self.wait()
            self.play(DrawTxt(frac))
            self.wait()
            self.play(ReplacementTransform(frac, dezi, run_time=0.5))
            self.wait()
            self.play(minus_tmp.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.play(minus_tmp.animate.set_color(WHITE_G).set_stroke(color=average_color(WHITE_G[0], WHITE_G[-1])),
                      eins.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      vier.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      sechs.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.play(eins.animate.set_color(WHITE_G).set_stroke(color=average_color(WHITE_G[0], WHITE_G[-1])),
                      vier.animate.set_color(WHITE_G).set_stroke(color=average_color(WHITE_G[0], WHITE_G[-1])),
                      sechs.animate.set_color(WHITE_G).set_stroke(color=average_color(WHITE_G[0], WHITE_G[-1])),
                      sieben.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      funf.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.play(sieben.animate.set_color(WHITE_G).set_stroke(color=average_color(WHITE_G[0], WHITE_G[-1])),
                      funf.animate.set_color(WHITE_G).set_stroke(color=average_color(WHITE_G[0], WHITE_G[-1])))
            self.wait()
            self.play(minus_tmp.animate.shift(3*LEFT),
                      eins.animate.shift(2*LEFT),
                      vier.animate.shift(1*LEFT),
                      comma.animate.shift(1*RIGHT),
                      sieben.animate.shift(2*RIGHT),
                      funf.animate.shift(3*RIGHT))
            self.wait()
            self.play(DrawTxt(einer.next_to(sechs, DOWN)))
            self.wait()
            self.play(DrawTxt(zehner.next_to(vier, DOWN)))
            self.wait()
            self.play(DrawTxt(hunderter.next_to(eins, DOWN)))
            self.wait()
            self.play(DrawTxt(zehntel.next_to(sieben, DOWN)))
            self.wait()
            self.play(DrawTxt(hundertstel.next_to(funf, DOWN)))
            self.wait()
            self.play(ReplacementTransform(hunderter, hunderter_.next_to(eins, DOWN*1.7)),
                      ReplacementTransform(zehner, zehner_.next_to(vier, DOWN*1.7)),
                      ReplacementTransform(einer, einer_.next_to(sechs, DOWN*1.7)),
                      ReplacementTransform(zehntel, zehntel_.next_to(sieben, DOWN*1.7)),
                      ReplacementTransform(hundertstel, hundertstel_.next_to(funf, DOWN*1.7))) 
            self.wait()      
            self.play(ReplacementTransform(hunderter_, hunderter_pot.next_to(eins, DOWN*1.7)),
                      ReplacementTransform(zehner_, zehner_pot.next_to(vier, DOWN*1.7)),
                      ReplacementTransform(einer_, einer_pot.next_to(sechs, DOWN*1.7)),
                      ReplacementTransform(zehntel_, zehntel_pot.next_to(sieben, DOWN*1.7)),
                      ReplacementTransform(hundertstel_, hundertstel_pot.next_to(funf, DOWN*1.7)))
            self.wait()
            self.play(FadeOut(hunderter_pot, zehner_pot, einer_pot, zehntel_pot, hundertstel_pot, minus_tmp, eins, vier, sechs, sieben, funf, *plus_signs[0:8], *(b.bulb_tex for b in bulbs[0:9])))
            b0.bulb_tex = potm5
            b1.bulb_tex = potm4
            b2.bulb_tex = potm3
            b3.bulb_tex = potm2
            b4.bulb_tex = potm1
            b5.bulb_tex = pot0.move_to([-0.5, 2.5, 0])
            b6.bulb_tex = pot1.move_to([-1.5, 2.5, 0])
            b7.bulb_tex = pot2.move_to([-2.5, 2.5, 0])
            b8.bulb_tex = pot3.move_to([-3.5, 2.5, 0])
            self.play(ReplacementTransform(comma, festes_comma))
            self.wait()
            self.play(festes_comma.animate.shift(UP*1.1))
            self.wait()
            self.play(DrawTxt(rect_around_ganz))
            self.wait()
            self.play(DrawTxt(b5.bulb_tex), DrawTxt(b6.bulb_tex), DrawTxt(b7.bulb_tex), DrawTxt(b8.bulb_tex), FadeIn(*(plus_signs[5:8])))
            self.wait()
            self.play(ReplacementTransform(rect_around_ganz, rect_around_bruch))
            self.wait()
            self.play(DrawTxt(b0.bulb_tex), DrawTxt(b1.bulb_tex), DrawTxt(b2.bulb_tex), DrawTxt(b3.bulb_tex), DrawTxt(b4.bulb_tex), FadeIn(*(plus_signs[0:4])))
            self.wait()
            self.play(FadeIn(plus_signs[4]), FadeOut(rect_around_bruch))
            for b in bulbs:
                b.bulb_tex_onscreen = True
            for i in range(4):
                orients[i].move_to([-0.5-i, 0.5, 0]).scale(0.65)
            self.play(FadeIn(orientm1,orientm2, orientm3, orientm4, orientm5, *orients[0:4]))
            self.wait()
            current_bubble_num = TexGen(r'4.125', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            self.play(BounceIn(person), BounceIn(speech))
            toggle([7, 2])
            self.play(DrawTxt(current_bubble_num))
            self.wait()
            toggle([4], sign=True)
            BubbleNum(r'-4.625')
            self.wait()
            self.play(Create(NL_Q1), FadeOut(current_bubble_num, speech, person), *[Create(d) for d in DOTS_Q1])
            self.wait()
            toggle([0, 1, 3, 5, 6, 8], sign=True)
            self.play(DrawTxt(NL_Q1_to))
            self.wait()
            toggle([], sign=True)
            self.play(DrawTxt(NL_Q1_from))
            self.wait()
            CAM.save_state()
            self.play(CAM.animate.move_to(NL_Q1.n2p(0.5)).scale(0.04), NL_Q1.animate.set_stroke(width=0.01), FadeIn(NL_Q1_small), run_time=1)
            self.wait()
            self.play(*(d.animate.shift(dot_move*UP*0.04) for d in DOTS_Q1[512:543]))
            self.play(DrawBorderThenFill(zahlen_31.next_to(DOTS_Q1[527], direction=UP*0.09), stroke_color=zahlen_31.get_stroke_colors(), stroke_width=0.1, run_time=1))
            self.wait()
            self.play(Restore(CAM), FadeOut(NL_Q1_small, zahlen_31, *DOTS_Q1), NL_Q1.animate.set_stroke(width=2))
            self.wait()
            toggle([0, 1, 2, 3, 4, 5, 6, 7, 8], sign=True)
            self.play(FadeOut(*(b.bulb_tex for b in bulbs), *orients[0:4], orientm1, orientm2, orientm3, orientm4, orientm5, NL_Q1, NL_Q1_from, NL_Q1_to))
            b0.bulb_tex = potm4.move_to([4.5, 2.5, 0])
            b1.bulb_tex = potm3.move_to([3.5, 2.5, 0])
            b2.bulb_tex = potm2.move_to([2.5, 2.5, 0])
            b3.bulb_tex = potm1.move_to([1.5, 2.5, 0])
            b4.bulb_tex = pot0.move_to([0.5, 2.5, 0])
            b5.bulb_tex = pot1.move_to([-0.5, 2.5, 0])
            b6.bulb_tex = pot2.move_to([-1.5, 2.5, 0])
            b7.bulb_tex = pot3.move_to([-2.5, 2.5, 0])
            b8.bulb_tex = pot4.move_to([-3.5, 2.5, 0])
            orient0.move_to([0.5, 0.5, 0])
            orient1.move_to([-0.5, 0.5, 0])
            orient2.move_to([-1.5, 0.5, 0])
            orient3.move_to([-2.5, 0.5, 0])
            orient4.move_to([-3.5, 0.5, 0]).scale(0.65)
            orientm1.move_to([1.5, 0.5, 0])
            orientm2.move_to([2.5, 0.5, 0])
            orientm3.move_to([3.5, 0.5, 0])
            orientm4.move_to([4.5, 0.5, 0])
            self.wait()
            self.play(festes_comma.animate.shift(1*RIGHT))
            self.play(FadeIn(*(b.bulb_tex for b in bulbs), *orients[0:5], orientm1, orientm2, orientm3, orientm4))
            self.wait()
            self.play(Create(NL_Q2), *[Create(d) for d in DOTS_Q2], DrawTxt(NL_Q2_to), DrawTxt(NL_Q2_from))
            CAM.save_state()
            self.wait()
            self.play(CAM.animate.move_to(NL_Q2.n2p(0.5)).scale(0.04), NL_Q2.animate.set_stroke(width=0.01), FadeIn(NL_Q2_small), run_time=1)
            self.play(*(d.animate.shift(dot_move*UP*0.04) for d in DOTS_Q2[512:527]))
            self.wait()
            self.play(DrawBorderThenFill(zahlen_15.next_to(DOTS_Q1[519], direction=UP*0.09), stroke_color=zahlen_15.get_stroke_colors(), stroke_width=0.1, run_time=1))
            self.wait()
            self.play(Restore(CAM), FadeOut(NL_Q2_small, zahlen_15, *DOTS_Q2), NL_Q2.animate.set_stroke(width=2))
            self.wait()
            self.play(FadeOut(NL_Q2, NL_Q2_from, NL_Q2_to, *orients[0:5], orientm1, orientm2, orientm3, orientm4))
            self.wait()
            self.play(DrawTxt(dezi_q2))
            self.play(BounceIn(dezi_q2_rpfeil), BounceIn(mal10))
            self.play(DrawTxt(dezi_q2_mal10))
            self.wait()
            self.play(ReplacementTransform(mal10, mal100), ReplacementTransform(dezi_q2_mal10, dezi_q2_mal100))
            self.wait()
            self.play(BounceIn(dezi_q2_lpfeil), BounceIn(mal10min))
            self.play(DrawTxt(dezi_q2_mal10min))
            self.wait()
            self.play(ReplacementTransform(mal10min, mal100min), ReplacementTransform(dezi_q2_mal10min, dezi_q2_mal100min))
            self.wait()
            self.play(FadeOut(mal100, dezi_q2_rpfeil, mal100min, dezi_q2_lpfeil, dezi_q2_mal100, dezi_q2_mal100min, dezi_q2))
            self.wait()
            self.play(DrawTxt(g_dezi))
            self.wait()
            self.play(ReplacementTransform(zehn, zwei.move_to(zehn.get_center())))
            self.wait()
            self.play(plus_minus.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      verschiebung.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      kommazahl.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]))) 
            self.wait()
            self.play(DrawTxt(rect_around_plus))
            self.wait()
            self.play(FadeOut(plus_minus))
            self.wait()
            self.play(ReplacementTransform(rect_around_plus, rect_around_bruch), FadeOut(plus_signs[4]))
            self.wait()
            self.play(FadeOut(kommazahl, cdot))
            self.wait()
            self.play(ReplacementTransform(rect_around_bruch, rect_around_ganz_cp))
            self.play(FadeOut(*(b.bulb_tex for b in bulbs[5:9])))
            self.wait()
            self.play(FadeOut(verschiebung))
            self.wait()
            self.play(ReplacementTransform(zwei, feste_zwei))
            self.play(DrawTxt(rect_around_exp))
            self.wait()
            b8.bulb_tex = plus_tmp
            b7.bulb_tex = pot2e
            b6.bulb_tex = pot1e
            b5.bulb_tex = pot0e
            self.play(FadeIn(*(b.bulb_tex for b in bulbs[5:9])), FadeOut(plus_signs[7]))
            b8.bulb_tex = pot3e
            self.wait()
            self.play(ReplacementTransform(plus_tmp, pot3e), FadeIn(plus_signs[7]))
            self.wait()
            self.play(FadeOut(rect_around_ganz_cp))
            self.play(DrawTxt(brace_bias))
            self.play(DrawTxt(bias))
            self.wait()
            self.play(DrawTxt(NL_0_15_from), DrawTxt(NL_0_15_to), Create(NL_0_15))
            self.play(*[Create(d) for d in DOTS_0_15])
            self.wait()
            self.play(BounceIn(darrow), BounceIn(bias3))
            self.play(FadeOut(t_Q_big))
            self.wait()
            self.play(DrawTxt(NL_bias_from), DrawTxt(NL_bias_to), Create(NL_bias))
            self.play(*[Create(d) for d in DOTS_bias])
            self.wait()
            self.play(ReplacementTransform(bias3, bias7), ReplacementTransform(NL_bias, NL_bias7), ReplacementTransform(NL_bias_to, NL_bias7_to), ReplacementTransform(NL_bias_from, NL_bias7_from))
            self.wait()
            self.play(ReplacementTransform(bias, bias_exp))
            self.wait()
            self.play(FadeOut(NL_0_15, NL_0_15_from, NL_0_15_to, NL_bias7, bias7, darrow, *DOTS_0_15, *DOTS_bias, NL_bias7_to, NL_bias7_from))
            self.play(FadeIn(t_Q_big))
            self.wait()
            self.play(BounceIn(person))
            self.wait()
            toggle([7, 6, 5, 4, 2], sign=True)
            current_bubble_num = TexGen(r'-1.25', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            self.play(DrawTxt(current_bubble_num), BounceIn(speech))
            self.wait()
            self.play(FadeOut(*plus_signs[5:8], bias_exp, brace_bias, *(b.bulb_tex for b in bulbs[5:9]), *(b.get_off_state() for b in bulbs[5:9]), *(b.get_on_state() for b in bulbs[5:8]), rect_around_exp, feste_zwei))
            self.wait()
            self.play(FadeIn(*plus_signs[5:8], bias_exp, brace_bias, *(b.bulb_tex for b in bulbs[5:9]), *(b.get_off_state() for b in bulbs[5:9]), *(b.get_on_state() for b in bulbs[5:8]), rect_around_exp, feste_zwei))
            self.wait()
            toggle([8, 7, 6, 5])
            BubbleNum(r'-2.5')
            self.wait()
            self.play(FadeOut(*plus_signs[5:8], bias_exp, brace_bias, *(b.bulb_tex for b in bulbs[5:9]), *(b.get_off_state() for b in bulbs[5:9]), b8.get_on_state(), rect_around_exp, feste_zwei))
            BubbleNum(r'-2.5?')
            self.wait()
            self.play(festes_comma.animate.shift(RIGHT),
                      ReplacementTransform(b0.bulb_tex, potm3_cp),
                      ReplacementTransform(b1.bulb_tex, potm2_cp),
                      ReplacementTransform(b2.bulb_tex, potm1_cp.set_color(YELL)),
                      ReplacementTransform(b3.bulb_tex, pot0_cp),
                      ReplacementTransform(b4.bulb_tex, pot1_cp.set_color(YELL)))
            BubbleNum(r'-2.5')
            self.wait()
            b0.bulb_tex = potm4_cp
            b1.bulb_tex = potm3_cp2
            b2.bulb_tex = potm2_cp2
            b3.bulb_tex = potm1_cp2
            b4.bulb_tex = pot0_cp2
            self.play(festes_comma.animate.shift(LEFT),
                      ReplacementTransform(potm3_cp, b0.bulb_tex),
                      ReplacementTransform(potm2_cp, b1.bulb_tex),
                      ReplacementTransform(potm1_cp, b2.bulb_tex.set_color(YELL)),
                      ReplacementTransform(pot0_cp, b3.bulb_tex),
                      ReplacementTransform(pot1_cp, b4.bulb_tex.set_color(YELL)),
                      FadeIn(*plus_signs[5:8], bias_exp, brace_bias, *(b.bulb_tex for b in bulbs[5:9]), *(b.get_off_state() for b in bulbs[5:9]), b8.get_on_state(), rect_around_exp, feste_zwei))
            self.wait()
            toggle([8, 7, 6, 5, 4, 2, 1], sign=True)
            BubbleNum(r'0.125')
            self.wait()
            toggle([2, 1])
            BubbleNum(r'0.25')
            self.wait()
            toggle([5])
            BubbleNum(r'0.125', col=RED_G)
            self.wait()
            toggle([3, 2])
            BubbleNum(r'0.25', col=RED_G)
            self.wait()
            toggle([6, 5])
            BubbleNum(r'0.125',col=RED_G)
            self.wait()
            toggle([4, 3])
            BubbleNum(r'0.25', col=RED_G)
            self.wait()
            toggle([5])
            BubbleNum(r'0.125',col=RED_G)
            self.wait()
            rect_around_bulbtex.move_to(b4.bulb_tex.get_center())
            self.play(DrawTxt(rect_around_bulbtex))
            self.wait()
            self.play(FadeOut(rect_around_bulbtex), FadeOut(current_bubble_num, speech))
            toggle([7, 4])
            self.wait()
            self.play(*(b.bulb_tex.animate.shift(RIGHT) for b in bulbs[0:5]), *(p.animate.shift(RIGHT) for p in plus_signs[0:4]), *(b.get_off_state().animate.shift(RIGHT) for b in bulbs[0:5]),
                      Transform(b0.bulb_tex, potm5_cp),
                      Transform(b1.bulb_tex, potm4_cp2),
                      Transform(b2.bulb_tex, potm3_cp3),
                      Transform(b3.bulb_tex, potm2_cp3),
                      Transform(b4.bulb_tex, potm1_cp3))
            self.play(DrawTxt(man_1_tmp), FadeOut(potm5_cp, potm4_cp2, potm3_cp3, potm2_cp3, potm1_cp3))
            self.wait()
            self.play(*(b.bulb_tex.animate.shift(LEFT) for b in bulbs[0:5]), *(p.animate.shift(LEFT) for p in plus_signs[0:4]), *(b.get_off_state().animate.shift(LEFT) for b in bulbs[0:5]),
                      ReplacementTransform(man_1_tmp, man_1), ReplacementTransform(festes_comma, man_1_comma))
            self.play(DrawTxt(darrow_man))
            self.wait()
            self.play(DrawTxt(brace_man), DrawTxt(mantisse_tmp))
            self.wait()
            current_bubble_num = TexGen(r'0.125', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            self.play(FadeOut(brace_man, mantisse_tmp))
            self.wait()
            toggle([7])
            self.play(BounceIn(speech), DrawTxt(current_bubble_num))
            self.wait()
            toggle([7])
            BubbleNum(r'0.0078125')
            self.wait()
            self.play(DrawTxt(special))
            self.wait()
            self.play(DrawTxt(exponent))
            man_1.save_state()
            self.play(DrawTxt(man_0_comma), ReplacementTransform(man_1, man_0), BounceIn(exp_offs))
            self.wait()
            BubbleNum(r'+0')
            self.wait()
            toggle([0])
            BubbleNum(r'0.000244140625', scale=0.5)
            self.wait()
            self.play(BounceIn(exp_ons))
            self.wait()
            self.play(DrawTxt(pm_inf))
            self.wait()
            toggle([8, 7, 6, 5, 0])
            self.play(ReplacementTransform(man_0, man1_cp))
            BubbleNum(r'+\infty')
            self.wait()
            toggle([2])
            BubbleNum(r'+\infty?')
            self.wait()
            self.play(DrawTxt(mantisse), BounceIn(man_offs))
            self.wait()
            self.play(BounceIn(exp_ons_cp), DrawTxt(neq0))
            self.wait()
            self.play(DrawTxt(nan))
            BubbleNum(r'\textup{NaN}')
            self.wait()
            toggle([0])
            BubbleNum(r'\textup{NaN?}')
            self.wait()
            toggle([], sign=True)
            BubbleNum(r'-\textup{NaN?}')
            self.wait()
            self.play(ReplacementTransform(nan, nans))
            self.wait()
            self.play(FadeOut(person, speech, current_bubble_num))
            self.wait()
            self.play(Create(NL_Q3), *[Create(d) for d in DOTS_Q3])
            self.wait()
            self.play(ReplacementTransform(DOTS_Q3[0], DOTS_Q3_neu[0]),
                      ReplacementTransform(DOTS_Q3[1], DOTS_Q3_neu[1]),
                      ReplacementTransform(DOTS_Q3[2], DOTS_Q3_neu[2]),
                      ReplacementTransform(DOTS_Q3[3], DOTS_Q3_neu[3]),
                      ReplacementTransform(DOTS_Q3[4], DOTS_Q3_neu[4]), run_time=3)
            self.wait()
            self.play(ReplacementTransform(DOTS_Q3_neu[0], DOTS_Q3_alt[0]),
                      ReplacementTransform(DOTS_Q3_neu[1], DOTS_Q3_alt[1]),
                      ReplacementTransform(DOTS_Q3_neu[2], DOTS_Q3_alt[2]),
                      ReplacementTransform(DOTS_Q3_neu[3], DOTS_Q3_alt[3]),
                      ReplacementTransform(DOTS_Q3_neu[4], DOTS_Q3_alt[4]), run_time=3)
            self.wait()
            toggle([8, 7, 6, 5, 2, 0], sign=True)
            self.play(ReplacementTransform(man1_cp, man0_cp))
            self.play(FadeOut(*DOTS_Q3_alt, NL_Q3, nans, mantisse, exponent, exp_offs, exp_ons, exp_ons_cp, pm_inf, neq0, special,
                              *(b.get_off_state() for b in bulbs), man_offs, feste_zwei, rect_around_exp, brace_bias, bias_exp, man0_cp, man_1_comma,
                              *plus_signs[0:4], *plus_signs[5:8], darrow_man, plus, t_Q_big, *(b.bulb_tex for b in bulbs[0:10]), man_0_comma))

        def play_RC(alone=False):
            nonlocal current_bubble_num;
            if alone:
                for b in bulbs:
                    b.change_y(1.5)
            self.play(DrawTxt(t_RC_big))
            self.play(t_RC_big.animate.move_to([-5, -3, 0]).scale(0.4))
            self.play(BounceIn([b.get_off_state() for b in bulbs]))
            self.wait()
            self.play(DrawTxt(pii))
            current_bubble_num = TexGen(r'3.125', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
            self.wait()
            toggle([8, 4, 1])
            self.play(BounceIn(person))
            self.play(BounceIn(speech), DrawTxt(current_bubble_num))
            self.wait()
            BubbleNum(r'\approx \pi')
            self.wait()
            self.play(FadeOut(pii, current_bubble_num, speech))
            toggle([8, 4, 1])
            self.wait()
            self.play(DrawTxt(cnum))
            self.wait()
            self.play(DrawTxt(abR))
            self.wait()
            self.play(ReplacementTransform(abR, abQ))
            self.wait()
            self.play(*(b.get_off_state().animate.shift(0.5*RIGHT) for b in bulbs[0:5]),
                      *(b.get_off_state().animate.shift(0.5*LEFT) for b in bulbs[5:10]))
            self.play(DrawTxt(plus_i))
            self.wait()
            self.play(FadeOut(*(b.get_off_state() for b in bulbs), plus_i, cnum, abQ, person, t_RC_big))
        
        def play_computer(alone=False):
            if alone:
                for b in bulbs:
                    b.change_y(1.5)
                b0.bulb_tex = potm5_cp.shift(LEFT)
                b1.bulb_tex = potm4_cp2.shift(LEFT)
                b2.bulb_tex = potm3_cp3.shift(LEFT)
                b3.bulb_tex = potm2_cp3.shift(LEFT)
                b4.bulb_tex = potm1_cp3.shift(LEFT)
                b7.bulb_tex = pot2e
                b6.bulb_tex = pot1e
                b5.bulb_tex = pot0e
                b8.bulb_tex = pot3e
            self.play(DrawTxt(digi))
            self.wait()
            self.play(BounceIn(person))
            self.wait()
            self.play(ShrinkToCenter(person, run_time=0.1), BounceIn(laptop))
            self.wait()
            self.play(BounceIn([b.get_off_state() for b in bulbs]))
            self.wait()
            digi.save_state()
            self.play(FadeIn(nans, mantisse, exponent, exp_offs, exp_ons, exp_ons_cp, pm_inf, neq0, special, man_offs, feste_zwei, rect_around_exp, brace_bias, bias_exp, man1_cp, man_1_comma,
                              *plus_signs[0:4], *plus_signs[5:8], darrow_man, plus, *(b.bulb_tex for b in bulbs[0:9]), man_1_comma, man_0_comma), digi.animate.to_corner(UR))
            self.wait()
            self.play(FadeOut(nans, mantisse, exponent, exp_offs, exp_ons, exp_ons_cp, pm_inf, neq0, special, man_offs, feste_zwei, rect_around_exp, brace_bias, bias_exp, man1_cp, man_1_comma,
                              *plus_signs[0:4], *plus_signs[5:8], darrow_man, plus, *(b.bulb_tex for b in bulbs[0:9]), man_1_comma, man_0_comma), Restore(digi))
            self.wait()
            b5.get_off_state().save_state()
            self.play(b5.get_off_state().animate.move_to([-1, 0, 0]))
            self.wait()
            self.play(BounceIn(transistor), DrawTxt(hat_eq))
            self.wait()
            self.play(DrawTxt(t_tran))
            self.wait()
            self.play(transistor.animate.shift(0.45*DOWN).scale(0))
            self.wait()
            self.play(Restore(b5.get_off_state()), FadeOut(hat_eq, t_tran))
            self.wait()
            toggle([0, 3, 7, 9])
            self.wait()
            self.play(FadeIn(bin_0, target_position=b0.get_off_state().get_center()),
                      FadeIn(bin_1, target_position=b1.get_off_state().get_center()),
                      FadeIn(bin_2, target_position=b2.get_off_state().get_center()),
                      FadeIn(bin_3, target_position=b3.get_off_state().get_center()),
                      FadeIn(bin_4, target_position=b4.get_off_state().get_center()),
                      FadeIn(bin_5, target_position=b5.get_off_state().get_center()),
                      FadeIn(bin_6, target_position=b6.get_off_state().get_center()),
                      FadeIn(bin_7, target_position=b7.get_off_state().get_center()),
                      FadeIn(bin_8, target_position=b8.get_off_state().get_center()),
                      FadeIn(bin_9, target_position=b9.get_off_state().get_center()))
            self.wait()
            self.play(FadeOut(laptop, bin_0, bin_1, bin_2, bin_3, bin_4, bin_5, bin_6, bin_7, bin_8, bin_9, *(b.get_off_state() for b in bulbs),
                              b0.get_on_state(), b3.get_on_state(), b7.get_on_state(), b9.get_on_state()))
            self.wait()
            self.play(FadeIn(txxt))
            self.play(FadeIn(speaker_l, note))
            self.play(FadeIn(pic))
            self.play(FadeIn(vid))
            self.wait()
            self.play(DrawTxt(numers_txt), DrawTxt(arrows_txt), DrawTxt(letters), DrawTxt(vdots_txt))
            self.wait()
            self.play(DrawTxt(numers_speaker), DrawTxt(arrows_speaker), DrawTxt(vdots_speaker))
            self.wait()
            self.play(FadeIn(speaker_ll), FadeIn(speaker_m), FadeIn(speaker_h))
            self.wait()
            self.play(DrawTxt(arrows_pic), DrawTxt(vdots_pic), FadeIn(pix1, pix2, pix3))
            self.wait()
            self.play(Create(ro), Create(gr), Create(bl))
            self.wait()
            self.play(DrawTxt(numers_pic))
            self.wait()
            for p in vid_pics:
                self.play(FadeIn(p), run_time=0.1)
            self.play(FadeIn(vid_sound))
            self.wait()
            self.play(FadeOut(digi))
            self.wait()
            self.play(DrawTxt(t_format), DrawTxt(s_format), DrawTxt(p_format), DrawTxt(v_format))
            self.wait()
            self.play(FadeOut(txxt, speaker_l, note, pic, vid, numers_txt, arrows_txt, letters, vdots_txt, t_format, s_format, p_format, v_format,
                              numers_speaker, arrows_speaker, vdots_speaker, speaker_ll, speaker_m, speaker_h,
                              arrows_pic, vdots_pic, pix1, pix2, pix3, ro, gr, bl, numers_pic, vid_sound, *vid_pics))
        
        def play_outro():
            self.play(Flash(point=snsus.get_center(), line_length=3, time_width=0.1, run_time=0.5), DrawTxt(snsus))       
            self.wait()
            self.play(snsus.animate.shift(2*UP))
            self.wait()
            self.play(BounceIn(masto))
            self.wait()
            self.play(FadeOut(masto))
            self.play(BounceIn(bmac))

            

        # VARIABLES
        b0 = Bulb(on=False, position=[4.5, 2.5, 0], bulb_tex=TexGen(r'1', isMath=True, font_sz=40, col=GRAY_G).move_to([4.5, 2.5, 0]))
        b1 = Bulb(on=False, position=[3.5, 2.5, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=GRAY_G).move_to([3.5, 2.5, 0]))
        b2 = Bulb(on=False, position=[2.5, 2.5, 0], bulb_tex=TexGen(r'3', isMath=True, font_sz=40, col=GRAY_G).move_to([2.5, 2.5, 0]))
        b3 = Bulb(on=False, position=[1.5, 2.5, 0], bulb_tex=TexGen(r'4', isMath=True, font_sz=40, col=GRAY_G).move_to([1.5, 2.5, 0]))
        b4 = Bulb(on=False, position=[0.5, 2.5, 0], bulb_tex=TexGen(r'5', isMath=True, font_sz=40, col=GRAY_G).move_to([0.5, 2.5, 0]))
        b5 = Bulb(on=False, position=[-0.5, 2.5, 0], bulb_tex=TexGen(r'6', isMath=True, font_sz=40, col=GRAY_G).move_to([-0.5, 2.5, 0]))
        b6 = Bulb(on=False, position=[-1.5, 2.5, 0], bulb_tex=TexGen(r'7', isMath=True, font_sz=40, col=GRAY_G).move_to([-1.5, 2.5, 0]))
        b7 = Bulb(on=False, position=[-2.5, 2.5, 0], bulb_tex=TexGen(r'8', isMath=True, font_sz=40, col=GRAY_G).move_to([-2.5, 2.5, 0]))
        b8 = Bulb(on=False, position=[-3.5, 2.5, 0], bulb_tex=TexGen(r'9', isMath=True, font_sz=40, col=GRAY_G).move_to([-3.5, 2.5, 0]))
        b9 = Bulb(on=False, position=[-4.5, 2.5, 0], bulb_tex=TexGen(r'10', isMath=True, font_sz=40, col=GRAY_G).move_to([-4.5, 2.5, 0]))
        bulbs = [b0, b1, b2, b3, b4, b5, b6, b7, b8, b9]
        g_bulbs = Group(*(b.get_off_state() for b in bulbs))
        b_wv_0 = Bulb(on=False, position=[-5, 1, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=WHITE_G).move_to([4.5, 3, 0]))
        b_wv_1 = Bulb(on=False, position=[-4, 1, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=WHITE_G).move_to([4.5, 3, 0]))
        b_wv_2 = Bulb(on=False, position=[-2, 1, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=WHITE_G).move_to([4.5, 3, 0]))
        b_wv_3 = Bulb(on=False, position=[-1, 1, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=WHITE_G).move_to([4.5, 3, 0]))
        b_wv_4 = Bulb(on=False, position=[1, 1, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=WHITE_G).move_to([4.5, 3, 0]))
        b_wv_5 = Bulb(on=False, position=[2, 1, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=WHITE_G).move_to([4.5, 3, 0]))
        b_wv_6 = Bulb(on=False, position=[4, 1, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=WHITE_G).move_to([4.5, 3, 0]))
        b_wv_7 = Bulb(on=False, position=[5, 1, 0], bulb_tex=TexGen(r'2', isMath=True, font_sz=40, col=WHITE_G).move_to([4.5, 3, 0]))
        paar_1 = Group(b_wv_0.get_off_state(), b_wv_1.get_off_state())
        paar_2 = Group(b_wv_2.get_off_state(), b_wv_3.get_on_state())
        paar_3 = Group(b_wv_4.get_on_state(), b_wv_5.get_off_state())
        paar_4 = Group(b_wv_6.get_on_state(), b_wv_7.get_on_state())
        paare = Group(paar_1, paar_2, paar_3, paar_4)
        exp_paar = Group(b8.bulb_tex, b7.bulb_tex, b6.bulb_tex, b5.bulb_tex)
        man_paar = Group(b4.bulb_tex, b3.bulb_tex, b2.bulb_tex, b1.bulb_tex, b0.bulb_tex)
        brace_paar_1 = Brace(paar_1, sharpness=1, stroke_width=1)
        brace_paar_2 = Brace(paar_2, sharpness=1, stroke_width=1)
        brace_paar_3 = Brace(paar_3, sharpness=1, stroke_width=1)
        brace_paar_4 = Brace(paar_4, sharpness=1, stroke_width=1)
        brace_paare = Brace(paare, sharpness=1, stroke_width=1)
        brace_10bulbs = Brace(g_bulbs, sharpness=1, stroke_width=1)
        brace_bias = Brace(exp_paar, sharpness=1, stroke_width=1, direction=UP).set_color(DGRAY_G).set_stroke(color=average_color(DGRAY_G[0], DGRAY_G[-1]))
        brace_man = Brace(man_paar, sharpness=1, stroke_width=1, direction=DOWN).set_color(WHITE_G).set_stroke(color=WHITE_G).shift(DOWN).shift(0.5*DOWN)
        
        person = ImageMobject('think.png').move_to([6, -3, 0])
        person.height = 1
        speech = ImageMobject('speech.png')
        speech.height = 2
        speech.next_to(person, UL, buff=-0.3).shift(0.3*DOWN)
        paper = ImageMobject('paper.png')
        paper.height = 3
        gif1 = GifImageMobject(filename="black5.gif").scale_to_fit_width(4).move_to([-4, 1.7, 0]) 
        gif2 = GifImageMobject(filename="black4.gif").scale_to_fit_width(4).move_to([4, 1.8, 0])
        gif3 = GifImageMobject(filename="black8.gif").scale_to_fit_width(5.5).move_to([-4, -2, 0])
        gif4 = GifImageMobject(filename="black9.gif").scale_to_fit_width(4).move_to([4, -2, 0]) 
        off_bulb0 = ImageMobject(filename_or_array="off.png")
        off_bulb0.height = b0.bulb_tex.height*1.4
        off_bulb1 = deepcopy(off_bulb0).next_to(off_bulb0, buff=-0.05)
        off_bulb2 = deepcopy(off_bulb0).next_to(off_bulb1, buff=-0.05)
        off_bulb3 = deepcopy(off_bulb0).next_to(off_bulb2, buff=-0.05)
        off_bulb4 = deepcopy(off_bulb0)
        off_bulb5 = deepcopy(off_bulb0).next_to(off_bulb4, buff=-0.05)
        off_bulb6 = deepcopy(off_bulb0).next_to(off_bulb5, buff=-0.05)
        off_bulb7 = deepcopy(off_bulb0).next_to(off_bulb6, buff=-0.05)
        off_bulb8 = deepcopy(off_bulb0).next_to(off_bulb7, buff=-0.05)
        exp_offs = Group(off_bulb0, off_bulb1, off_bulb2, off_bulb3)
        man_offs = Group(off_bulb4, off_bulb5, off_bulb6, off_bulb7, off_bulb8)
        on_bulb0 = ImageMobject(filename_or_array="on.png")
        on_bulb0.height = b0.bulb_tex.height*1.4
        on_bulb1 = deepcopy(on_bulb0).next_to(on_bulb0, buff=-0.05)
        on_bulb2 = deepcopy(on_bulb0).next_to(on_bulb1, buff=-0.05)
        on_bulb3 = deepcopy(on_bulb0).next_to(on_bulb2, buff=-0.05)
        exp_ons = Group(on_bulb0, on_bulb1, on_bulb2, on_bulb3)
        cat = ImageMobject(filename_or_array="cat.jpg")
        cat.height = 3
        catv = VideoMobject(filename="catv.mp4")
        catv.height = 3
        speaker_l = ImageMobject(filename_or_array="low.png").move_to([-1.5, 1, 0])
        speaker_m = ImageMobject(filename_or_array="medi.png")
        speaker_h = ImageMobject(filename_or_array="high.png")
        speaker_l.height = 2
        speaker_m.height = 0.55
        speaker_h.height = 0.55
        txxt = ImageMobject(filename_or_array="txt.png").move_to([-4.5, 1, 0])
        txxt.height = 2
        pic = ImageMobject(filename_or_array="pic.png").move_to([1.5, 1, 0])
        pic.height = 2
        pic1 = deepcopy(pic)
        pic1.height = 1
        pic2 = deepcopy(pic1).next_to(pic1, DR, buff=-0.9)
        pic3 = deepcopy(pic1).next_to(pic2, DR, buff=-0.9)
        pic4 = deepcopy(pic1).next_to(pic3, DR, buff=-0.9)
        pic5 = deepcopy(pic1).next_to(pic4, DR, buff=-0.9)
        pic6 = deepcopy(pic1).next_to(pic5, DR, buff=-0.9)
        vid = ImageMobject(filename_or_array="vid.png").move_to([4.5, 1, 0])
        vid.height = 2
        vid_pics = Group(pic1, pic2, pic3, pic4, pic5, pic6).next_to(vid, 2.5*DOWN)
        note = ImageMobject(filename_or_array="note.png")
        note.height = 1
        note.next_to(speaker_l, UR, buff=-0.8)
        bmac_t =  TexGen(r'Du würdest mich supporten?', isMath=False, font_sz=45)
        bmac_p = ImageMobject(filename_or_array="kofi.png")
        bmac_p.height = 1
        bmac_t2 =  TexGen(r'ko-fi.com/snsus', isMath=False).scale_to_fit_width(bmac_p.width)
        masto_p = ImageMobject(filename_or_array="masto.png")
        masto_p.height = 1
        mas_t = TexGen(r'mastodon.social/@snsus', isMath=False, font_sz=45)
        bmac = Group(bmac_p.next_to(bmac_t, DOWN), bmac_t, bmac_t2.next_to(bmac_p, DOWN)).move_to(ORIGIN).shift(DOWN)
        masto = Group(masto_p, mas_t.next_to(masto_p, DOWN)).move_to(ORIGIN).shift(DOWN)
        laptop = ImageMobject(filename_or_array="laptop.png")
        laptop.height = 1
        laptop.move_to(person.get_center())

        t_damit = TexGen(r'Represent')
        t_zahlen = TexGen(r'Numbers').next_to(t_damit, RIGHT).shift(0.041*UP)
        t_darst = TexGen(r'with them?').next_to(t_zahlen, RIGHT).shift(0.015*UP)
        g_damitzd = VGroup(t_damit, t_zahlen, t_darst).move_to(ORIGIN).shift(1*UP)
        t_N_small = TexGen(r'\mathbb{N}', isMath=True, col=YEBLUE_G).next_to(t_zahlen, DOWN).shift(0.5*DOWN)
        t_N_nums = TexGen(r'1, 2, 3, \ldots', isMath=True).next_to(t_N_small, RIGHT, buff=0.5).shift(0.05*DOWN)
        t_Z_small = TexGen(r'\mathbb{Z}', isMath=True, col=YEBLUE_G).next_to(t_N_small, DOWN)
        t_Z_nums = TexGen(r'\ldots, -2, \ldots', isMath=True).next_to(t_Z_small, RIGHT, buff=0.5).shift(0.05*DOWN)
        t_Q_small = TexGen(r'\mathbb{Q}', isMath=True, col=YEBLUE_G).next_to(t_Z_small, DOWN)
        t_Q_nums = TexGen(r'$\ldots, \frac{1}{2}, \ldots$').next_to(t_Q_small, RIGHT, buff=0.5).shift(0.05*DOWN+0.04*LEFT)
        t_R_small = TexGen(r'\mathbb{R}', isMath=True, col=YEBLUE_G).next_to(t_Q_small, DOWN)
        t_R_nums = TexGen(r'\ldots, \pi, \ldots', isMath=True).next_to(t_R_small, RIGHT, buff=0.5).shift(0.12*DOWN+0.03*LEFT)
        t_C_small = TexGen(r'\mathbb{C}', isMath=True, col=YEBLUE_G).next_to(t_R_small, DOWN)
        t_C_nums = TexGen(r'\ldots, 3+2i, \ldots', isMath=True).next_to(t_C_small, RIGHT, buff=0.5).shift(0.05*DOWN+0.03*LEFT)
        intro_nums = VGroup(t_N_small, t_N_nums, t_Z_small, t_Z_nums, t_Q_small, t_Q_nums, t_R_small, t_R_nums, t_C_small, t_C_nums)
        t_N_big = TexGen(r'\mathbb{N}', isMath=True, font_sz=300, col=YEBLUE_G)
        t_Z_big = TexGen(r'\mathbb{Z}', isMath=True, font_sz=300, col=YEBLUE_G)
        t_Q_big = TexGen(r'\mathbb{Q}', isMath=True, font_sz=300, col=YEBLUE_G)
        t_RC_big = TexGen(r'\mathbb{R}\text{ }\&\text{ }\mathbb{C}', isMath=True, font_sz=300, col=YEBLUE_G)
        t_N0_big = TexGen(r'\mathbb{N}_0', isMath=True, font_sz=300, col=YEBLUE_G).move_to([-6, -3, 0]).scale(0.4)
        t_anzahl = TexGen(r'number $\widehat{=}$ number of lit light bulbs')
        t_stelle = TexGen(r'number $\widehat{=}$ position of a lit light bulb')
        plus_signs = [TexGen(r'+', isMath=True, font_sz=35, col=GRAY_G).move_to([4-i, 2.5, 0]) for i in range(9)]
        t_wv = TexGen(r'How many numbers?')
        t_paar_1 = TexGen(r'some\\ number').next_to(brace_paar_1, DOWN)
        t_paar_2 = TexGen(r'another\\ number').next_to(brace_paar_2, DOWN)
        t_paar_3 = TexGen(r'another one').next_to(brace_paar_3, DOWN)
        t_paar_4 = TexGen(r'last one').next_to(brace_paar_4, DOWN)
        t_paare = TexGen(r'4 different numbers').next_to(brace_paare, DOWN)
        t_mogl1 = TexGen(r'$\uparrow$\\2').next_to(b_wv_1.get_off_state(), DOWN)
        t_mogl2 = TexGen(r'$\uparrow$\\2').next_to(b_wv_0.get_off_state(), DOWN)
        t_mogl3 = TexGen(r'$\uparrow$\\2')
        t_mogl_cdot1 = TexGen(r'\cdot', isMath=True).move_to([-4.5, -0.5, 0]).shift(0.05*DOWN)
        t_mogl_cdot2 = TexGen(r'\cdot', isMath=True).move_to([-3.5, -0.5, 0]).shift(0.05*DOWN)
        t_mogl_eq = TexGen(r'=', isMath=True).move_to([-3.4, -0.5, 0])
        t_mogl_4 = TexGen(r'4', isMath=True).next_to(t_mogl_eq, RIGHT)
        t_mogl_8 = TexGen(r'8', isMath=True).shift(0.05*DOWN)
        t_2hochanzahl_eq = TexGen(r'=', isMath=True).move_to([-1.3, -0.5, 0]).shift(0.05*DOWN)
        t_2hochanzahl_zahl = TexGen(r'2^{\textup{number of light bulbs}}', isMath=True).next_to(t_2hochanzahl_eq, RIGHT).shift(0.08*UP)
        t_mogl_ges = VGroup(t_mogl_eq, t_mogl_4).shift(0.05*DOWN)
        t_mogl_ges_8 = VGroup(t_2hochanzahl_eq, t_2hochanzahl_zahl)
        t_10Bulbs_mogl = TexGen(r'2^{10} = 1024 \textup{ different numbers}', isMath=True).next_to(brace_10bulbs, DOWN)
        current_bubble_num = TexGen(r'3', isMath=True, font_sz=100, col=YEBLUE_G).scale_to_fit_height(0.7).move_to(speech.get_center()).shift(0.1*UP)
        pot0 = TexGen(r'2^{0}', isMath=True, font_sz=40, col=GRAY_G).move_to([4.5, 2.5, 0])
        pot1 = TexGen(r'2^{1}', isMath=True, font_sz=40, col=GRAY_G).move_to([3.5, 2.5, 0])
        pot2 = TexGen(r'2^{2}', isMath=True, font_sz=40, col=GRAY_G).move_to([2.5, 2.5, 0])
        pot3 = TexGen(r'2^{3}', isMath=True, font_sz=40, col=GRAY_G).move_to([1.5, 2.5, 0])
        pot4 = TexGen(r'2^{4}', isMath=True, font_sz=40, col=GRAY_G).move_to([0.5, 2.5, 0])
        pot5 = TexGen(r'2^{5}', isMath=True, font_sz=40, col=GRAY_G).move_to([-0.5, 2.5, 0])
        pot6 = TexGen(r'2^{6}', isMath=True, font_sz=40, col=GRAY_G).move_to([-1.5, 2.5, 0])
        pot7 = TexGen(r'2^{7}', isMath=True, font_sz=40, col=GRAY_G).move_to([-2.5, 2.5, 0])
        pot8 = TexGen(r'2^{8}', isMath=True, font_sz=40, col=GRAY_G).move_to([-3.5, 2.5, 0])
        pot9 = TexGen(r'2^{9}', isMath=True, font_sz=40, col=GRAY_G).move_to([-4.5, 2.5, 0])
        potm1 = TexGen(r'2^{-1}', isMath=True, font_sz=40, col=GRAY_G).move_to([0.5, 2.5, 0])
        potm2 = TexGen(r'2^{-2}', isMath=True, font_sz=40, col=GRAY_G).move_to([1.5, 2.5, 0])
        potm3 = TexGen(r'2^{-3}', isMath=True, font_sz=40, col=GRAY_G).move_to([2.5, 2.5, 0])
        potm4 = TexGen(r'2^{-4}', isMath=True, font_sz=40, col=GRAY_G).move_to([3.5, 2.5, 0])
        potm5 = TexGen(r'2^{-5}', isMath=True, font_sz=40, col=GRAY_G).move_to([4.5, 2.5, 0])
        pot0e = TexGen(r'2^{0}', isMath=True, font_sz=40, col=GRAY_G).move_to([-3.5, 2.5, 0]).move_to([-0.5, 2.5, 0])
        pot1e = TexGen(r'2^{1}', isMath=True, font_sz=40, col=GRAY_G).move_to([-2.5, 2.5, 0]).move_to([-1.5, 2.5, 0])
        pot2e = TexGen(r'2^{2}', isMath=True, font_sz=40, col=GRAY_G).move_to([-1.5, 2.5, 0]).move_to([-2.5, 2.5, 0])
        pot3e = TexGen(r'2^{3}', isMath=True, font_sz=40, col=GRAY_G).move_to([-1.5, 2.5, 0]).move_to([-3.5, 2.5, 0])
        potm4_cp = TexGen(r'2^{-4}', isMath=True, font_sz=40, col=GRAY_G).move_to([4.5, 2.5, 0])
        potm3_cp = TexGen(r'2^{-3}', isMath=True, font_sz=40, col=GRAY_G).move_to([4.5, 2.5, 0])
        potm2_cp = TexGen(r'2^{-2}', isMath=True, font_sz=40, col=GRAY_G).move_to([3.5, 2.5, 0])
        potm1_cp = TexGen(r'2^{-1}', isMath=True, font_sz=40, col=GRAY_G).move_to([2.5, 2.5, 0])
        pot0_cp = TexGen(r'2^{0}', isMath=True, font_sz=40, col=GRAY_G).move_to([1.5, 2.5, 0])
        pot1_cp = TexGen(r'2^{1}', isMath=True, font_sz=40, col=GRAY_G).move_to([0.5, 2.5, 0])
        potm3_cp2 = TexGen(r'2^{-3}', isMath=True, font_sz=40, col=GRAY_G).move_to([3.5, 2.5, 0])
        potm2_cp2 = TexGen(r'2^{-2}', isMath=True, font_sz=40, col=GRAY_G).move_to([2.5, 2.5, 0])
        potm1_cp2 = TexGen(r'2^{-1}', isMath=True, font_sz=40, col=GRAY_G).move_to([1.5, 2.5, 0])
        pot0_cp2 = TexGen(r'2^{0}', isMath=True, font_sz=40, col=GRAY_G).move_to([0.5, 2.5, 0])
        potm5_cp = TexGen(r'2^{-5}', isMath=True, font_sz=40, col=GRAY_G).move_to([5.5, 2.5, 0])
        potm4_cp2 = TexGen(r'2^{-4}', isMath=True, font_sz=40, col=GRAY_G).move_to([4.5, 2.5, 0])
        potm3_cp3 = TexGen(r'2^{-3}', isMath=True, font_sz=40, col=GRAY_G).move_to([3.5, 2.5, 0])
        potm2_cp3 = TexGen(r'2^{-2}', isMath=True, font_sz=40, col=GRAY_G).move_to([2.5, 2.5, 0])
        potm1_cp3 = TexGen(r'2^{-1}', isMath=True, font_sz=40, col=GRAY_G).move_to([1.5, 2.5, 0])


        orient0 = TexGen(r'1', isMath=True, font_sz=40, col=DGRAY_G).move_to([4.5, 0.5, 0])
        orient1 = TexGen(r'2', isMath=True, font_sz=40, col=DGRAY_G).move_to([3.5, 0.5, 0])
        orient2 = TexGen(r'4', isMath=True, font_sz=40, col=DGRAY_G).move_to([2.5, 0.5, 0])
        orient3 = TexGen(r'8', isMath=True, font_sz=40, col=DGRAY_G).move_to([1.5, 0.5, 0])
        orient4 = TexGen(r'16', isMath=True, font_sz=40, col=DGRAY_G).move_to([0.5, 0.5, 0])
        orient5 = TexGen(r'32', isMath=True, font_sz=40, col=DGRAY_G).move_to([-0.5, 0.5, 0])
        orient6 = TexGen(r'64', isMath=True, font_sz=40, col=DGRAY_G).move_to([-1.5, 0.5, 0])
        orient7 = TexGen(r'128', isMath=True, font_sz=40, col=DGRAY_G).move_to([-2.5, 0.5, 0])
        orient8 = TexGen(r'256', isMath=True, font_sz=40, col=DGRAY_G).move_to([-3.5, 0.5, 0])
        orient9 = TexGen(r'512', isMath=True, font_sz=40, col=DGRAY_G).move_to([-4.5, 0.5, 0])
        orientm1 = TexGen(r'.5', isMath=True, font_sz=40, col=DGRAY_G).move_to([0.5, 0.5, 0]).scale(0.65) 
        orientm2 = TexGen(r'.25', isMath=True, font_sz=40, col=DGRAY_G).move_to([1.5, 0.5, 0]).scale(0.65) 
        orientm3 = TexGen(r'.125', isMath=True, font_sz=40, col=DGRAY_G).move_to([2.5, 0.5, 0]).scale(0.65) 
        orientm4 = TexGen(r'.0625', isMath=True, font_sz=40, col=DGRAY_G).move_to([3.5, 0.5, 0]).scale(0.65) 
        orientm5 = TexGen(r'.03125', isMath=True, font_sz=40, col=DGRAY_G).move_to([4.5, 0.5, 0]).scale(0.65) 
        orients = [orient0, orient1, orient2, orient3, orient4, orient5, orient6, orient7, orient8, orient9]
        plus = TexGen(r'+', isMath=True, font_sz=50, col=YEBLUE_G).move_to(pot9.get_center())
        minus = TexGen(r'-', isMath=True, font_sz=50, col=YEBLUE_G).move_to(pot9.get_center())
        minus_tmp = TexGen(r'-', isMath=True, col=WHITE_G)
        eins = TexGen(r'1', isMath=True, col=WHITE_G).next_to(minus_tmp, RIGHT, buff=0.07)
        vier = TexGen(r'4', isMath=True, col=WHITE_G).next_to(eins, RIGHT, buff=0.07)
        sechs = TexGen(r'6', isMath=True, col=WHITE_G).next_to(vier, RIGHT, buff=0.07)
        comma = TexGen(r'.', isMath=True, col=WHITE_G).next_to(sechs, DR, buff=0.1).shift(0.12*UP)
        sieben = TexGen(r'7', isMath=True, col=WHITE_G).next_to(sechs, RIGHT, buff=0.26)
        funf = TexGen(r'5', isMath=True, col=WHITE_G).next_to(sieben, RIGHT, buff=0.07)
        dezi = VGroup(minus_tmp, eins, vier, sechs, comma, sieben, funf).move_to(ORIGIN)
        festes_minus = TexGen(r'-', isMath=True, font_sz=100, col=YEBLUE_G).move_to([-5.5, 1.5, 0])
        festes_comma = TexGen(r'.', isMath=True, font_sz=100, col=YEBLUE_G)
        feste_zwei = TexGen(r'2', isMath=True, font_sz=50, col=YEBLUE_G).move_to([-3.8, 0.7, 0])
        frac = TexGen(r'-\frac{587}{4}', isMath=True, col=WHITE_G)
        einer = TexGen(r'$\downarrow$\\1s', font_sz=40)
        zehner = TexGen(r'$\downarrow$\\10s', font_sz=40)
        hunderter = TexGen(r'$\downarrow$\\100s',font_sz=40)
        zehntel = TexGen(r'$\downarrow$\\10ths', font_sz=40)
        hundertstel = TexGen(r'$\downarrow$\\100ths', font_sz=40)
        einer_ = TexGen(r'$\cdot$\\1', font_sz=40)
        zehner_ = TexGen(r'$\cdot$\\10', font_sz=40)
        hunderter_ = TexGen(r'$\cdot$\\100',font_sz=40)
        zehntel_ = TexGen(r'$\cdot$\\$\frac{1}{10}$', font_sz=40)
        hundertstel_ = TexGen(r'$\cdot$\\$\frac{1}{100}$', font_sz=40)
        einer_pot = TexGen(r'$\cdot$\\$10^{0}$', font_sz=40)
        zehner_pot = TexGen(r'$\cdot$\\$10^{1}$', font_sz=40)
        hunderter_pot = TexGen(r'$\cdot$\\$10^{2}$',font_sz=40)
        zehntel_pot = TexGen(r'$\cdot$\\$10^{-1}$', font_sz=40)
        hundertstel_pot = TexGen(r'$\cdot$\\$10^{-2}$', font_sz=40)
        plus_null = MathTex(r'+0', font_size=3).set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1]), width=0.1).shift(0.04*UP + 0.03*RIGHT)
        minus_null = MathTex(r'-0', font_size=3).set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1]), width=0.1).shift(0.04*UP + 0.03*LEFT)
        lim = MathTex(r'\lim_{x \to \phantom{-0}} \frac{1}{x}', font_size=3).set_stroke(width=0.1).shift(DOWN*0.1)
        lim_plusinf = MathTex(r'= +\infty', font_size=3).set_stroke(width=0.1).next_to(lim, buff=0.015).shift(0.0037*DOWN)
        lim_minusinf = MathTex(r'= -\infty', font_size=3).set_stroke(width=0.1).next_to(lim, buff=0.015).shift(0.0037*DOWN)
        zahlen_31 = Tex(r'31 numbers', font_size=3).set_color(WHITE_G).set_stroke(color=average_color(WHITE_G[0], WHITE_G[-1]), width=0.1)
        zahlen_15 = Tex(r'15 numbers', font_size=3).set_color(WHITE_G).set_stroke(color=average_color(WHITE_G[0], WHITE_G[-1]), width=0.1)
        dezi_q2 = TexGen(r'381.279', isMath=True, col=WHITE_G)
        dezi_q2_rpfeil = TexGen(r'\rightarrow', isMath=True, col=WHITE_G, font_sz=75).next_to(dezi_q2)
        mal10 = TexGen(r'\cdot 10^{\phantom{2}}', isMath=True, col=WHITE_G, font_sz=40).next_to(dezi_q2_rpfeil, DOWN)
        dezi_q2_mal10 = TexGen(r'3812.79', isMath=True, col=WHITE_G).next_to(dezi_q2_rpfeil)
        mal100 = TexGen(r'\cdot 10^{2}', isMath=True, col=WHITE_G, font_sz=40).next_to(dezi_q2_rpfeil, DOWN)
        dezi_q2_mal100 = TexGen(r'38127.9', isMath=True, col=WHITE_G).next_to(dezi_q2_rpfeil)
        dezi_q2_lpfeil = TexGen(r'\leftarrow', isMath=True, col=WHITE_G, font_sz=75).next_to(dezi_q2, LEFT)
        mal10min = TexGen(r'\cdot 10^{-1}', isMath=True, col=WHITE_G, font_sz=40).next_to(dezi_q2_lpfeil, DOWN)
        dezi_q2_mal10min = TexGen(r'38.1279', isMath=True, col=WHITE_G).next_to(dezi_q2_lpfeil, LEFT)
        mal100min = TexGen(r'\cdot 10^{-2}', isMath=True, col=WHITE_G, font_sz=40).next_to(dezi_q2_lpfeil, DOWN)
        dezi_q2_mal100min = TexGen(r'3.81279', isMath=True, col=WHITE_G).next_to(dezi_q2_lpfeil, LEFT)
        zehn = TexGen(r'10 \phantom{.}', isMath=True, col=WHITE_G)
        zwei = TexGen(r'2 \phantom{.}', isMath=True, col=WHITE_G)
        verschiebung = TexGen(r'point shift', isMath=False, col=WHITE_G, font_sz=38).next_to(zehn, UR, buff=0.04).shift(0.1*DOWN)
        g_10_e = VGroup(zehn, verschiebung)
        plus_minus = TexGen(r'\pm', isMath=True, col=WHITE_G).next_to(g_10_e, LEFT)
        cdot = TexGen(r'\cdot \phantom{,}', isMath=True, col=WHITE_G).next_to(g_10_e)
        kommazahl = TexGen(r'decimal number', isMath=False, col=WHITE_G).next_to(cdot)
        g_dezi = VGroup(plus_minus, g_10_e.shift(0.15*UP),  cdot, kommazahl).move_to(ORIGIN)
        plus_tmp = TexGen(r'+', isMath=True, font_sz=50, col=YEBLUE_G).move_to([-3.5, 2.5, 0])
        bias = TexGen(r'-\textup{Bias}', isMath=True, col=YEBLUE_G).next_to(brace_bias, UP, buff=0.15).shift(0.05*LEFT)
        darrow = TexGen(r'\downarrow', isMath=True, col=WHITE_G, font_sz=75).shift(2*DOWN)
        bias3 = TexGen(r'-3', isMath=True, col=YEBLUE_G).next_to(darrow)
        bias7 = TexGen(r'-7', isMath=True, col=YEBLUE_G).next_to(darrow)
        bias_exp = TexGen(r'-7', isMath=True, col=YEBLUE_G).next_to(brace_bias, UP, buff=0.15).shift(0.05*LEFT)
        man_1_tmp = TexGen(r'1', isMath=True, font_sz=100, col=YEBLUE_G).move_to([0.5, 1.5, 0])
        man_1 = TexGen(r'1', isMath=True, col=YEBLUE_G).set_y(bias_exp.get_y())
        man1_cp = deepcopy(man_1)
        man_0 = TexGen(r'0', isMath=True, col=YEBLUE_G).set_y(bias_exp.get_y())  
        man0_cp = deepcopy(man_0)
        man_1_comma = TexGen(r'.', isMath=True, col=YEBLUE_G).next_to(man_1, DR, buff=0).shift(0.05*UP+0.05*RIGHT)
        darrow_man = TexGen(r'\downarrow', isMath=True, col=DGRAY_G, font_sz=45).next_to(man_1, DOWN).set_stroke(width=2)
        mantisse_tmp = TexGen('Mantissa', isMath=False).next_to(brace_man, DOWN)
        special = TexGen('Special case', font_sz=40, isMath=False, col=YEBLUE_G).shift(5.6*LEFT)
        exponent = TexGen('Exponent', font_sz=40, isMath=False).next_to(special, buff=0.5)
        mantisse = TexGen(r'Mantissa', font_sz=40, isMath=False).next_to(exponent, buff=0.5).shift(0.03*UP)
        man_0_comma = TexGen(r'0.', font_sz=40, isMath=True, col=YEBLUE_G).next_to(special, DOWN)
        pm_inf = TexGen(r'\pm \infty', font_sz=40, isMath=True, col=YEBLUE_G).next_to(man_0_comma, DOWN)
        exp_offs.next_to(exponent, DOWN)
        exp_ons.next_to(exp_offs, DOWN)
        exp_ons_cp = deepcopy(exp_ons).next_to(exp_ons, DOWN)
        man_offs.next_to(mantisse, DOWN).set_y(exp_ons.get_y())
        neq0 = TexGen(r'\neq 0', font_sz=40, isMath=True, col=WHITE_G).next_to(man_offs, DOWN)
        nan = TexGen(r'\textup{NaN}', font_sz=40, isMath=True, col=YEBLUE_G).next_to(pm_inf, DOWN).set_y(neq0.get_y())
        nans = TexGen(r'\textup{NaN\textquotesingle s}', font_sz=40, isMath=True, col=YEBLUE_G).next_to(pm_inf, DOWN).set_y(neq0.get_y())
        pii = TexGen(r'\pi = 3.1415926535 \ldots', isMath=True)
        cnum = TexGen(r'a+ib', isMath=True)
        abR = TexGen(r'a, b \in \mathbb{R}', isMath=True).shift(DOWN)
        abQ = TexGen(r'a, b \in \mathbb{Q}', isMath=True).shift(DOWN)
        plus_i = TexGen(r'+i', isMath=True, col=YEBLUE_G, font_sz=100).set_y(1.5)
        digi = TexGen(r'Digital World?').set_y(3)
        arrows_txt = TexGen(r'$\rightarrow$\\$\rightarrow$\\$\rightarrow$', isMath=False, font_sz=45).next_to(txxt, DOWN*2.5)
        numers_txt = TexGen(r'1\\2\\3', isMath=False, col=YEBLUE_G, font_sz=45).next_to(arrows_txt, LEFT)
        letters = TexGen(r'A\\B\\C', isMath=False, font_sz=45).next_to(arrows_txt, RIGHT)
        vdots_txt = TexGen(r'\vdots', isMath=True, font_sz=45).next_to(arrows_txt, DOWN)
        arrows_speaker = deepcopy(arrows_txt).next_to(speaker_l, DOWN*2.5).shift(0.3*LEFT)
        arrows_pic = deepcopy(arrows_txt).next_to(pic, DOWN*2.5).shift(0.6*RIGHT)
        numers_speaker = deepcopy(numers_txt).next_to(arrows_speaker, LEFT)
        vdots_speaker = deepcopy(vdots_txt).next_to(arrows_speaker, DOWN)
        vdots_pic = deepcopy(vdots_txt).next_to(arrows_pic, DOWN)
        speaker_ll = deepcopy(speaker_l)
        speaker_ll.height = 0.55
        speaker_ll.move_to([-1.1, -0.7, 0])
        speaker_m.move_to([-1.1, -1.3, 0])
        speaker_h.move_to([-1.1, -1.9, 0])
        pix1 = Square(0.4).set_color(PIX_blue).move_to([2.7, -0.75, 0]).set_fill(color=PIX_blue, opacity=1).set_stroke(width=0)
        pix2 = Square(0.4).set_color(PIX_green).move_to([2.7, -1.3, 0]).set_fill(color=PIX_green, opacity=1).set_stroke(width=0)
        pix3 = Square(0.4).set_color(PIX_yell).move_to([2.7, -1.85, 0]).set_fill(color=PIX_yell, opacity=1).set_stroke(width=0)
        fz = 45
        n0 = TexGen(r')\\)\\)', isMath=False, col=WHITE_G, font_sz=fz).next_to(arrows_pic, LEFT)
        n1 = TexGen(r'3\\6\\9', isMath=False, col=YEBLUE_G, font_sz=fz).next_to(n0, LEFT, buff=0.1)
        n2 = TexGen(r',\\,\\,', isMath=False, col=WHITE_G, font_sz=fz).next_to(n1, LEFT, buff=0.15).shift(0.2*DOWN)
        n3 = TexGen(r'2\\5\\8', isMath=False, col=YEBLUE_G, font_sz=fz).next_to(n2, LEFT, buff=0.05).shift(0.2*UP)
        n4 = TexGen(r',\\,\\,', isMath=False, col=WHITE_G, font_sz=fz).next_to(n3, LEFT, buff=0.15).shift(0.2*DOWN)
        n5 = TexGen(r'1\\4\\7', isMath=False, col=YEBLUE_G, font_sz=fz).next_to(n4, LEFT, buff=0.05).shift(0.2*UP)
        n6 = TexGen(r'(\\(\\(', isMath=False, col=WHITE_G, font_sz=fz).next_to(n5, LEFT, buff=0.1)
        numers_pic = VGroup(n0, n1, n2, n3, n4, n5, n6)
        vid_sound = Group(deepcopy(speaker_l), deepcopy(note))
        vid_sound.height = 1
        vid_sound.next_to(vid_pics, DOWN)
        ro = Circle(0.1, color=PRED).set_fill(color=PRED, opacity=1).set_stroke(width=0).next_to(n5, UP)
        gr = Circle(0.1, color=PGREEN).set_fill(color=PGREEN, opacity=1).set_stroke(width=0).next_to(n3, UP)
        bl = Circle(0.1, color=PBLUE).set_fill(color=PBLUE, opacity=1).set_stroke(width=0).next_to(n1, UP)
        hat_eq = TexGen(r'\widehat{=}', isMath=True, font_sz=90)
        bin_0 = TexGen(r'1', isMath=True, font_sz=90).next_to(b0.get_off_state(), 5*DOWN)
        bin_1 = TexGen(r'0', isMath=True, font_sz=90).next_to(b1.get_off_state(), 5*DOWN)
        bin_2 = TexGen(r'0', isMath=True, font_sz=90).next_to(b2.get_off_state(), 5*DOWN)
        bin_3 = TexGen(r'1', isMath=True, font_sz=90).next_to(b3.get_off_state(), 5*DOWN)
        bin_4 = TexGen(r'0', isMath=True, font_sz=90).next_to(b4.get_off_state(), 5*DOWN)
        bin_5 = TexGen(r'0', isMath=True, font_sz=90).next_to(b5.get_off_state(), 5*DOWN)
        bin_6 = TexGen(r'0', isMath=True, font_sz=90).next_to(b6.get_off_state(), 5*DOWN)
        bin_7 = TexGen(r'1', isMath=True, font_sz=90).next_to(b7.get_off_state(), 5*DOWN)
        bin_8 = TexGen(r'0', isMath=True, font_sz=90).next_to(b8.get_off_state(), 5*DOWN)
        bin_9 = TexGen(r'1', isMath=True, font_sz=90).next_to(b9.get_off_state(), 5*DOWN)
        t_format = TexGen(r'.txt', isMath=False, font_sz=45).next_to(txxt, UP*2)
        s_format = TexGen(r'.mp3', isMath=False, font_sz=45).next_to(Group(speaker_l, note), UP*2).set_y(t_format.get_y())
        p_format = TexGen(r'.png', isMath=False, font_sz=45).next_to(pic, UP*2)
        v_format = TexGen(r'.mp4', isMath=False, font_sz=45).next_to(vid, UP*2)

        rect_around_bulbtex = RoundedRectangle(corner_radius=0.1, height=b2.bulb_tex.height*1.9, width=b2.bulb_tex.height*1.9).set_color(YEBLUE_G).set_stroke(color=YEBLUE_G).move_to(b2.bulb_tex.get_center())
        rect_around_ganz = RoundedRectangle(corner_radius=0.1, height=b2.bulb_tex.height*2, width=3.7).set_color(YEBLUE_G).set_stroke(color=YEBLUE_G).move_to(b7.bulb_tex.get_center()).shift(0.5*RIGHT)
        rect_around_ganz_cp = deepcopy(rect_around_ganz)
        rect_around_bruch = RoundedRectangle(corner_radius=0.1, height=b2.bulb_tex.height*2, width=5).set_color(YEBLUE_G).set_stroke(color=YEBLUE_G).move_to(b2.bulb_tex.get_center())
        rect_around_plus = RoundedRectangle(corner_radius=0.1, height=b9.bulb_tex.height*1.9, width=b9.bulb_tex.height*1.9).set_color(YEBLUE_G).set_stroke(color=YEBLUE_G).move_to(b9.bulb_tex.get_center())
        rect_around_exp = DashedVMobject(RoundedRectangle(corner_radius=0.1, height=1.65, width=4).set_color(DGRAY_G).set_stroke(color=DGRAY_G).move_to(b7.bulb_tex.get_center()).shift(0.5*RIGHT+1.25*DOWN), num_dashes=50)
        trn_up = RoundedRectangle(corner_radius=0.4, height=2.5, width=2.5).set_color(TRN_col_up).set_stroke(color=TRN_col_up).set_fill(color=TRN_col_up, opacity=1)
        line = RoundedRectangle(corner_radius=0.2, height=1.5, width=0.28).set_color(TRN_col_down).set_stroke(color=TRN_col_down).set_fill(color=TRN_col_down, opacity=1).next_to(trn_up, DOWN, buff=0).set_z_index(-1).shift(0.15*UP)
        line_l = deepcopy(line).next_to(line, LEFT, buff=0.28)
        line_r = deepcopy(line).next_to(line, RIGHT, buff=0.28)
        transistor = VGroup(trn_up, line, line_l, line_r).scale(0.24).move_to([1, 0, 0])
        t_tran = TexGen(r'Transistor', isMath=False, font_sz=50).next_to(transistor, buff=0.5)
        snsus = TexGen(r'snsus', isMath=False, font_sz=200)

        curv_arrows = []
        t_doubles = []
        for i in range(9):
            curv_arrows.append(VGroup(CurvedArrow([4.3-i, 2.9, 0], [3.7-i, 2.9, 0], tip_length=0.1, tip_shape=StealthTip)))
            t_doubles.append(TexGen(r'\cdot 2', isMath=True, font_sz=40).next_to(plus_signs[i], UP, buff=0.55))

        dot_move = 0.3
        NL_0_10 = NumberLine([0, 10, 1], label_direction=DOWN*1.4, numbers_with_elongated_ticks=[0, 10], longer_tick_multiple=0, numbers_to_exclude=[0, 10], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False})
        DOTS_0_10 = [Dot(NL_0_10.number_to_point(i), radius=0.1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1) for i in range(11)]
        NL_0_10_from = TexGen(r'0', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_10[0], DOWN)
        NL_0_10_to = TexGen(r'10', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_10[-1], DOWN)

        NL_0_15 = NumberLine([0, 15, 1], label_direction=DOWN*1.4, numbers_with_elongated_ticks=[0, 15], longer_tick_multiple=0, numbers_to_exclude=[0, 15], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).shift(0.5*DOWN)
        DOTS_0_15 = [Dot(NL_0_15.number_to_point(i), radius=0.1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1) for i in range(16)]
        NL_0_15_from = TexGen(r'0', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_15[0], DOWN)
        NL_0_15_to = TexGen(r'15', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_15[-1], DOWN)

        NL_bias = NumberLine([-3, 12, 1], label_direction=DOWN*1.4, numbers_with_elongated_ticks=[-3, 12], longer_tick_multiple=0, numbers_to_exclude=[-3, 12], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).shift(3*DOWN)
        DOTS_bias = [Dot(NL_bias.number_to_point(i), radius=0.1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1) for i in np.linspace(-3, 12, num=16)]
        NL_bias_from = TexGen(r'-3', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_bias[0], DOWN)
        NL_bias_to = TexGen(r'12', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_bias[-1], DOWN)

        NL_bias7 = NumberLine([-7, 8, 1], label_direction=DOWN*1.4, numbers_with_elongated_ticks=[-7, 8], longer_tick_multiple=0, numbers_to_exclude=[-7, 8], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).shift(3*DOWN)
        DOTS_bias7 = [Dot(NL_bias7.number_to_point(i), radius=0.1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1) for i in np.linspace(-7, 8, num=16)]
        NL_bias7_from = TexGen(r'-7', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_bias7[0], DOWN)
        NL_bias7_to = TexGen(r'8', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_bias7[-1], DOWN)
        
        NL_0_55 = NumberLine([0, 55, 5], label_direction=DOWN*1.4, numbers_with_elongated_ticks=[0, 55], longer_tick_multiple=0, numbers_to_exclude=[0, 55], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False})
        DOTS_0_55 = [Dot(NL_0_55.number_to_point(i), radius=0.1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1) for i in range(56)]
        DOT_56 = Dot(radius=0.1).next_to(DOTS_0_55[55], RIGHT, buff=0).shift(dot_move*UP).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1)
        NL_0_55_from = TexGen(r'0', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[0], DOWN)
        NL_0_55_to = TexGen(r'55', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[-1], DOWN)
        NL_0_55_to56 = TexGen(r'56', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOT_56, DOWN).shift(dot_move*DOWN)
        
        NL_0_1023 = NumberLine([0, 1023, 1023], numbers_with_elongated_ticks=[0, 1023], longer_tick_multiple=0, numbers_to_exclude=[0, 1023], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False})
        DOTS_0_1023 = [Dot(NL_0_1023.number_to_point(i), radius=0.005).set_z_index(1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])) for i in range(1024)]
        NL_0_1023_from = TexGen(r'0', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[0], DOWN)
        NL_0_1023_to = TexGen(r'1023', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[-1], DOWN)
        NL_0_1023_small = NumberLine([0, 1023, 10], label_direction=DOWN*0.09, numbers_with_elongated_ticks=[0, 1023], longer_tick_multiple=0, font_size=2, stroke_width=0.09, tick_size=0.015, numbers_to_exclude=[0, 1023], length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).set_z_index(-1)

        NL_minus1023 = NumberLine([-1023, 0, 1023], numbers_with_elongated_ticks=[-1023, 0], longer_tick_multiple=0, numbers_to_exclude=[-1023, 0], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False})
        NL_minus1023_from = TexGen(r'-1023', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[0], DOWN)
        NL_minus1023_to = TexGen(r'0', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[-1], DOWN)

        NL_minus511 = NumberLine([-511, 511, 1023], exclude_origin_tick=True, numbers_with_elongated_ticks=[-511, 511], longer_tick_multiple=0, numbers_to_exclude=[-511, 511], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False})
        DOTS_minus511 = [Dot(NL_minus511.number_to_point(i), radius=0.005).set_z_index(1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])) for i in range(-511, 511)]
        NL_minus511_from = TexGen(r'-511', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[0], DOWN)
        NL_minus511_to = TexGen(r'511', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[-1], DOWN)
        DOTS_minus511[511].set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1]))
        NL_minus511_small = NumberLine([-511, 511, 10], label_direction=DOWN*0.09, numbers_with_elongated_ticks=[-511, 511], longer_tick_multiple=0, font_size=2, stroke_width=0.09, tick_size=0.015, numbers_to_exclude=[-511, 511], length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).set_z_index(-1)
        DOT_minus_null = Dot(NL_minus511.number_to_point(-0.25), radius=0.005).set_z_index(1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])).shift(dot_move*UP*0.04)
        DOT_plus_null = Dot(NL_minus511.number_to_point(0.25), radius=0.005).set_z_index(1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])).shift(dot_move*UP*0.04)
        g_null_dots = VGroup(DOT_minus_null, DOT_plus_null)

        NL_Q1 = NumberLine([-15.96875, 15.96875, 31.9375], exclude_origin_tick=True, numbers_with_elongated_ticks=[-15.96875, 15.96875], longer_tick_multiple=0, numbers_to_exclude=[-15.96875, 15.96875], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).shift(DOWN)
        DOTS_Q1 = [Dot(NL_Q1.number_to_point(i), radius=0.005).set_z_index(1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])) for i in np.linspace(-15.96875, 15.96875, num=1023)]
        NL_Q1_from = TexGen(r'-15.96875', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[0], DOWN).shift(DOWN)
        NL_Q1_to = TexGen(r'15.96875', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[-1], DOWN).shift(DOWN)
        DOTS_Q1[511].set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1]))
        NL_Q1_small = NumberLine([-15.96875, 15.96875, 1], label_direction=DOWN*0.09, numbers_with_elongated_ticks=[-15.96875, 15.96875], longer_tick_multiple=0, font_size=2, stroke_width=0.09, tick_size=0.015, numbers_to_exclude=[-15.96875, 15.96875], length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).set_z_index(-1).shift(DOWN)

        NL_Q2 = NumberLine([-31.9375, 31.9375, 63.875], exclude_origin_tick=True, numbers_with_elongated_ticks=[-31.9375, 31.9375], longer_tick_multiple=0, numbers_to_exclude=[-31.9375, 31.9375], tick_size=0.2, length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).shift(DOWN)
        DOTS_Q2 = [Dot(NL_Q2.number_to_point(i), radius=0.005).set_z_index(1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])) for i in np.linspace(-31.9375, 31.9375, num=1023)]
        NL_Q2_from = TexGen(r'-31.9375', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[0], DOWN).shift(DOWN)
        NL_Q2_to = TexGen(r'31.9375', isMath=True, font_sz=42, col=YEBLUE_G).next_to(DOTS_0_55[-1], DOWN).shift(DOWN)
        DOTS_Q2[511].set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1]))
        NL_Q2_small = NumberLine([-31.9375, 31.9375, 1], label_direction=DOWN*0.09, numbers_with_elongated_ticks=[-31.9375, 31.9375], longer_tick_multiple=0, font_size=2, stroke_width=0.09, tick_size=0.015, numbers_to_exclude=[-31.9375, 31.9375], length=12, include_numbers=True, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).set_z_index(-1).shift(DOWN)

        NL_Q3 = NumberLine([-5, 5, 1], label_direction=DOWN*1.4, numbers_with_elongated_ticks=[-5, 5], longer_tick_multiple=0, numbers_to_exclude=[0, 10], tick_size=0.2, length=6, include_numbers=False, decimal_number_config={"num_decimal_places": 0, "group_with_commas": False}).next_to(mantisse, buff=0.6)
        DOTS_Q3 = [Dot(NL_Q3.number_to_point(i), radius=0.1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1) for i in np.linspace(-1, 1, num=5)]
        DOTS_Q3_neu = [Dot(NL_Q3.number_to_point(i), radius=0.1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1) for i in np.linspace(-5, 5, num=5)]
        DOTS_Q3_alt = [Dot(NL_Q3.number_to_point(i), radius=0.1).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1]), width=1) for i in np.linspace(-1, 1, num=5)]
        

        # ANIMATE
        self.wait()
        play_intro()
        play_N()
        play_WV(alone=False)
        play_N_next(alone=False)
        play_Z(alone=True)
        play_Q(alone=True)
        play_RC(alone=True)
        play_computer(alone=True)
        play_outro()
        self.wait()



