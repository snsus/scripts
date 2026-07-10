import cv2
import numpy as np
from manim import *
from copy import deepcopy
from PIL import Image, ImageOps
from PIL import GifImagePlugin
from dataclasses import dataclass
from itertools import combinations
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
        YEW_G = color_gradient([ManimColor.from_hex("#FFF5C2"), ManimColor.from_hex("#FFE76C")], 200)
        YEBLUE_G = color_gradient([ManimColor.from_hex("#FFED95"), ManimColor.from_hex("#16E3F9")], 200)
        RYEBLUE_G = color_gradient([ManimColor.from_hex("#16E3F9"), ManimColor.from_hex("#FFED95")], 200)
        GR_G = color_gradient([ManimColor.from_hex("#5F5F5F"), ManimColor.from_hex("#949494")], 200)
        RGR_G = color_gradient([ManimColor.from_hex("#949494"), ManimColor.from_hex("#5F5F5F")], 200)
        GREEN_G = color_gradient([ManimColor.from_hex("#BFFF97"), ManimColor.from_hex("#00C849")], 200)
        RED_G = color_gradient([ManimColor.from_hex("#F18097"), ManimColor.from_hex("#DE002C")], 200)
        RRED_G = color_gradient([RED_G[-1], RED_G[0]], 200)
        MAG_G = color_gradient([ManimColor.from_hex("#FFBDFE"), ManimColor.from_hex("#FF68FC")], 200)
        SILV_G= color_gradient([ManimColor.from_hex("#949494"), ManimColor.from_hex("#FFFFFF")], 200)
        LSILV_G= color_gradient([ManimColor.from_hex("#BEBEBE"), ManimColor.from_hex("#FFFFFF")], 200)
        YELL_G = color_gradient([ManimColor.from_hex("#FFFFB3"), ManimColor.from_hex("#FFC44E")], 200)
        RYELL_G = color_gradient([ManimColor.from_hex("#FFC44E"), ManimColor.from_hex("#FFFFB3")], 200)
        BR_G = color_gradient([ManimColor.from_hex("#FFBC75"), ManimColor.from_hex("#A45B17")], 200)
        CUBE_G = color_gradient([ManimColor.from_hex("#FFD279"), ManimColor.from_hex("#FFC44E")], 200)
        

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
        
        def wordGen(str):
            word = VGroup()
            word.add(TexGen(rf'{str[0]}', font_sz=100, col=YELL_G))
            for letter in str[1:]:
                word.add(TexGen(rf'{letter}', font_sz=100, col=YELL_G).next_to(word[-1], RIGHT, buff=0.06, aligned_edge=DOWN))
            return word
        
        def SetGen(elements, tup=False, col=WHITE_G, vgroup=True):
            if tup:
                open_bracket = TexGen(r'(', col=col).scale_to_fit_height(elements[0].height*(1.2))
                closing_bracket = TexGen(r')', col=col).scale_to_fit_height(elements[0].height*(1.2))
            else:
                open_bracket = TexGen(r'\{', col=col).scale_to_fit_height(elements[0].height*(1.3))
                closing_bracket = TexGen(r'\}', col=col).scale_to_fit_height(elements[0].height*(1.3))
            if vgroup:
                set_to_return = VGroup(open_bracket, elements[0].next_to(open_bracket, buff=0.1))
            else:
                set_to_return = Group(open_bracket, elements[0].next_to(open_bracket, buff=0.1))
            if len(elements) == 1:
                return set_to_return.add(closing_bracket.next_to(elements[-1], buff=0.1))
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
            set_to_return.add(closing_bracket.next_to(elements[-1], buff=0.1))
            return set_to_return
        
        def QTransform(pos):
            rnd[pos].save_state()
            return Transform(rnd[pos], deepcopy(Qm).move_to(rnd[pos], aligned_edge=DOWN))
        
        def Dice(num, scl=0.2, col=YELL_G) -> VMobject:
            R = RoundedRectangle(1, width=5.5, height=5.5).set_color(col).set_stroke(col).set_fill(col, opacity=1)
            C = Circle(0.5).set_color(BLACK_G).set_stroke(BLACK_G).set_fill(BLACK_G, opacity=1)
            match num:
                case 1:
                    return VGroup(deepcopy(R), deepcopy(C)).scale(scl)
                case 2:
                    return(VGroup(deepcopy(R), deepcopy(C).shift(1.5*(LEFT+DOWN)), deepcopy(C).shift(1.5*(RIGHT+UP)))).scale(scl)
                case 3:
                    return(VGroup(deepcopy(R), deepcopy(C), deepcopy(C).shift(1.5*(LEFT+DOWN)), deepcopy(C).shift(1.5*(RIGHT+UP)))).scale(scl)
                case 4:
                    return(VGroup(deepcopy(R), deepcopy(C).shift(1.5*(LEFT+DOWN)), deepcopy(C).shift(1.5*(LEFT+UP)), deepcopy(C).shift(1.5*(RIGHT+DOWN)), deepcopy(C).shift(1.5*(RIGHT+UP)))).scale(scl)
                case 5:
                    return(VGroup(deepcopy(R), deepcopy(C), deepcopy(C).shift(1.5*(LEFT+DOWN)), deepcopy(C).shift(1.5*(LEFT+UP)), deepcopy(C).shift(1.5*(RIGHT+DOWN)), deepcopy(C).shift(1.5*(RIGHT+UP)))).scale(scl)
                case 6:
                    return(VGroup(deepcopy(R), deepcopy(C).shift(1.5*LEFT), deepcopy(C).shift(1.5*RIGHT), deepcopy(C).shift(1.5*(LEFT+DOWN)), deepcopy(C).shift(1.5*(LEFT+UP)), deepcopy(C).shift(1.5*(RIGHT+DOWN)), deepcopy(C).shift(1.5*(RIGHT+UP)))).scale(scl)

        rot_point = [0, 2.2, 0]
        out_line = RoundedRectangle(0.02, width=0.04, height=2.2-0.8).set_color(GR_G).set_fill(GR_G, opacity=1).set_stroke(GR_G).move_to(rot_point, aligned_edge=UP)    
        
        def BranchLine(dx, r_point=rot_point, height=out_line.height):
            return deepcopy(out_line).stretch_to_fit_height(np.sqrt(dx**2+height**2)).move_to(r_point, aligned_edge=UP).rotate(-np.arctan(dx/height), about_point=r_point)
        
        def PowerSet(S, n_elements):
            return [list(c) for c in combinations(S, n_elements)]
        
        # Video Segments
        def play_intro():
            rect = RoundedRectangle(0.5, height=9*0.6, width=16*0.6).set_stroke(width=10, color=YEBLUE_G).set_fill(opacity=0).next_to(prob, DOWN).shift(0.3*DOWN).set_z_index(-1)
            black_rect = RoundedRectangle(0.6, height=9*0.64, width=16*0.62).set_stroke(width=35, color=BLACK_G).set_fill(opacity=0).move_to(rect).set_z_index(-2)
            fade_rect = RoundedRectangle(0.6, height=9*0.64, width=16*0.62).set_stroke(width=35, color=BLACK_G).set_fill(opacity=1, color=BLACK_G).move_to(rect).set_z_index(-2.1)
            self.add(fade_rect)
            weather = VideoMobject("weather.mp4").set_z_index(-3).scale_to_fit_width(rect.width).move_to(rect)
            traffic = VideoMobject("traffic.mp4").set_z_index(-2.9).scale_to_fit_width(rect.width).move_to(rect)
            market = VideoMobject("market.mp4").set_z_index(-2.8).scale_to_fit_width(rect.width).move_to(rect)
            ai = VideoMobject("ai.mp4").set_z_index(-2.7).scale_to_fit_width(rect.width).move_to(rect)
            quantum = VideoMobject("quantum.mp4").set_z_index(-2.6).scale_to_fit_width(rect.width).move_to(rect)
            decision = VideoMobject("decision.mp4").set_z_index(-2.5).scale_to_fit_width(rect.width).move_to(rect)
            med = VideoMobject("med.mp4").set_z_index(-2.4).scale_to_fit_width(rect.width).move_to(rect)
            nolife = VideoMobject("nolife.mp4").set_z_index(-2.3).scale_to_fit_width(rect.width).move_to(rect)
            self.play(Draw(prob.move_to(ORIGIN)))
            prob_cp = deepcopy(prob)
            self.wait()
            self.add(black_rect)
            self.add(weather)
            grow_point = prob.get_edge_center(DOWN)
            self.play(LaggedStart(AnimationGroup(prob.animate.to_edge(UP), GrowFromPoint(rect, point=grow_point)), FadeOut(fade_rect), lag_ratio=0.8))
            self.wait()
            self.add(traffic)
            self.remove(weather)
            self.wait()
            self.add(market)
            self.remove(traffic)
            self.wait(1.5)
            self.add(ai)
            self.remove(market)
            self.wait(1.5)
            self.add(quantum)
            self.remove(ai)
            self.wait(1.5)
            self.add(decision)
            self.remove(quantum)
            self.wait(3)
            self.add(med)
            self.remove(decision)
            self.wait(1.5)
            self.add(nolife)
            self.remove(med)
            self.wait(2)
            cube = Cube(1, fill_color=YEBLUE_G, fill_opacity=1).set_color(YEBLUE_G).set_stroke(width=1, color=YEW_G).rotate(-0.1*PI, axis=UP+LEFT)
            q = TexGen(r'?', font_sz=100, col=YEBLUE_G).next_to(cube, DOWN).shift(0.5*DOWN)
            v = TexGen(r'Volume', font_sz=100, col=YEBLUE_G).move_to(q)
            self.play(Group(nolife, rect, black_rect).animate.scale(0).move_to(grow_point), prob.animate.move_to(ORIGIN))
            self.remove(nolife)
            self.play(Draw(q))
            self.wait()
            self.play(prob.animate.become(cube), ReplacementTransform(q, v))
            self.wait()
            self.play(prob.animate.become(prob_cp), FadeOut(v))
            self.wait()

        def play_random():
            self.add(prob.move_to(ORIGIN))
            p = TexGen(r'P', isMath=True, font_sz=100, col=YEBLUE_G)
            self.play(ReplacementTransform(prob, p))
            self.wait()
            finger = TexGen(r'\ding{42}', col=YEBLUE_G, font_sz=120).rotate(PI/2).shift(rnd.get_center()/2*UP)
            quant = TexGen(r'quantify', col=YEBLUE_G, font_sz=50).next_to(finger, LEFT)
            whatever = Text('whatever', font="RUBBERSTAMP", font_size=50).move_to(rnd).set_color(RED_G).rotate(PI/9)
            self.play(GrowFromPoint(VGroup(finger, quant), [0, 0.7, 0]))
            self.play(Draw(rnd), FadeOut(quant))
            self.wait()
            q_time = 1
            self.play(QTransform(6))
            self.play(Restore(rnd[6]), QTransform(3), run_time=q_time)
            self.play(Restore(rnd[3]), QTransform(8), run_time=q_time)
            self.play(Restore(rnd[8]), QTransform(1), run_time=q_time)
            self.play(QTransform(5), run_time=q_time)
            self.play(Restore(rnd[1]), QTransform(6), run_time=q_time)
            self.play(Restore(rnd[5]), QTransform(0), QTransform(3), run_time=q_time)
            self.play(Restore(rnd[0]), Restore(rnd[6]), QTransform(9), run_time=q_time)
            self.play(Restore(rnd[3]), QTransform(4), QTransform(2), run_time=q_time)
            self.play(Restore(rnd[9]), Restore(rnd[4]), QTransform(1), run_time=q_time)
            self.play(Restore(rnd[2]), QTransform(0), run_time=q_time)
            self.play(Restore(rnd[0]), QTransform(8), QTransform(4), QTransform(6), run_time=q_time)
            self.play(Restore(rnd[1]), QTransform(9), QTransform(3), QTransform(2), run_time=q_time)
            self.play(Restore(rnd[6]), Restore(rnd[9]), run_time=q_time)
            self.play(QTransform(1), Restore(rnd[8]), run_time=q_time)
            self.play(Restore(rnd[2]), run_time=q_time)
            self.play(QTransform(5), QTransform(9), Restore(rnd[4]), run_time=q_time)
            self.play(QTransform(2), QTransform(6), run_time=q_time)
            self.play(QTransform(8), Restore(rnd[3]), run_time=q_time)
            self.play(QTransform(3), QTransform(7), Restore(rnd[2]), run_time=q_time)
            self.play(QTransform(4), Restore(rnd[6]), run_time=q_time)
            self.play(QTransform(2), QTransform(6), run_time=q_time)
            self.play(Draw(whatever), run_time=0.3)
            self.wait()
            p_buff = 0.5
            p_line = RoundedRectangle(0.02, width=0.04, height=1).set_color(RYEBLUE_G).set_fill(opacity=1, color=RYEBLUE_G).set_stroke(RYEBLUE_G).next_to(p, DOWN, buff=p_buff)
            certain = TexGen(r'Certainty', font_sz=50, col=YEBLUE_G).next_to(p_line, DOWN, buff=p_buff-0.2)
            num_line = RoundedRectangle(0.02, width=9, height=0.04).set_stroke(GR_G).set_fill(opacity=1, color=GR_G).rotate(PI).set_z_index(-1)
            tick0 = RoundedRectangle(0.02, width=0.04, height=0.7).set_stroke(GR_G[0]).set_fill(opacity=1, color=GR_G[0]).shift(num_line.width/2*LEFT)
            tick100 = deepcopy(tick0).shift(num_line.width*RIGHT).set_stroke(GR_G[-1]).set_fill(opacity=1, color=GR_G[-1])
            interval = VGroup(num_line, tick0, tick100).move_to(p_line)
            zero = TexGen(r'0', isMath=True, font_sz=100, col=GR_G)
            zero_pc = VGroup(zero, deepcopy(pc).next_to(zero, RIGHT, buff=0.1)).scale(0.5).next_to(tick0, DOWN)
            hundred = TexGen(r'100', isMath=True, font_sz=100, col=GR_G)
            hundred_pc = VGroup(hundred, deepcopy(pc).next_to(hundred, RIGHT, buff=0.1)).scale(0.5).next_to(tick100, DOWN)
            self.play(GrowFromPoint(VGroup(p_line, certain), [0, -0.6, 0]))
            self.wait()
            self.play(GrowFromCenter(interval))
            self.play(GrowFromPoint(zero_pc, tick0.get_edge_center(DOWN), point_color=BLACK), GrowFromPoint(hundred_pc, tick100.get_edge_center(DOWN), point_color=BLACK))
            p.add_updater(lambda mob: mob.next_to(p_line, UP, buff=p_buff))
            certain.add_updater(lambda mob: mob.next_to(p_line, DOWN, buff=p_buff-0.2))
            finger.add_updater(lambda mob: mob.set_x(p_line.get_x()*0.4))
            self.play(p_line.animate.shift(1.5*LEFT), p.animate.scale(0.5), certain.animate.scale(0.5), Rotate(finger, -PI/5), run_time=2)
            self.play(p_line.animate.shift(3*RIGHT), p.animate.scale(4), certain.animate.scale(4), Rotate(finger, 2*PI/5), run_time=2)
            self.play(p_line.animate.shift(1.5*LEFT), p.animate.scale(0.5), certain.animate.scale(0.5), Rotate(finger, -PI/5), run_time=2)
            self.wait()
            self.play(zero_pc[1].animate.set_color(RED_G), hundred_pc[1].animate.set_color(RED_G))
            self.wait()
            pc1_0 = TexGen(r'1', isMath=True, col=RED_G).scale_to_fit_height(zero_pc[1][0].height-0.01)
            pc1_100 = deepcopy(pc1_0)
            self.play(zero_pc[1][0].animate.next_to(zero_pc[1][1], LEFT, buff=0.04).shift(0.4*RIGHT), hundred_pc[1][0].animate.next_to(hundred_pc[1][1], LEFT, buff=0.04).shift(0.4*RIGHT),
                      zero_pc[1][1].animate.shift(0.4*RIGHT), hundred_pc[1][1].animate.shift(0.4*RIGHT))
            self.play(Draw(pc1_0.next_to(zero_pc[1][0], LEFT, buff=0.05)), Draw(pc1_100.next_to(hundred_pc[1][0], LEFT, buff=0.05)))
            self.wait()
            new_zero = TexGen(r'0', font_sz=100, col=YEBLUE_G).scale(0.5).move_to(zero).set_x(tick0.get_x())
            one = TexGen(r'1', font_sz=100, col=YEBLUE_G).scale(0.5).move_to(hundred).set_x(tick100.get_x())
            interval_align = TexGen(r'[0, 1]', col=RED_G, isMath=True, font_sz=100).scale(0.5).move_to(certain)
            interval_from = TexGen(r'[', col=YEBLUE_G, isMath=True, font_sz=100).scale(0.5).move_to(interval_align, aligned_edge=LEFT)
            interval_to = TexGen(r']', col=YEBLUE_G, isMath=True, font_sz=100).scale(0.5).move_to(interval_align, aligned_edge=RIGHT)
            comma = TexGen(r',', col=YEBLUE_G, isMath=True, font_sz=100).scale(0.5).move_to(interval_align, aligned_edge=DOWN).shift(0.02*UP+0.04*LEFT)
            self.play(ReplacementTransform(VGroup(zero_pc, pc1_0), new_zero), ReplacementTransform(VGroup(hundred_pc, pc1_100), one))
            self.wait()
            p.clear_updaters()
            certain.clear_updaters()
            brackets = TexGen(r'\phantom{P}(\phantom{\textup{Event}})', isMath=True, font_sz=100, col=YEBLUE_G).shift(0.43*RIGHT+0.01*DOWN)
            event = TexGen(r'\phantom{P}\phantom{(}\textup{Event}\phantom{)}', isMath=False, col=YELL_G, font_sz=100).set_z_index(-1).move_to(brackets).shift(0.1*UP)
            self.play(GrowFromCenter(brackets), p.animate.shift(1.7*LEFT+0.08*UP))
            self.play(GrowFromPoint(event, rnd.get_center()))
            self.play(ReplacementTransform(tick0, interval_from), ReplacementTransform(tick100, interval_to), ReplacementTransform(num_line, comma),
                      certain.animate.next_to(interval_align, DOWN),
                      new_zero.animate.move_to(interval_align).shift(0.26*LEFT+0.04*UP).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      one.animate.move_to(interval_align).shift(0.26*RIGHT+0.04*UP).set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.wait()
            self.play(FadeOut(p, event, finger, p_line, certain, new_zero, one, interval_from, interval_to, comma, brackets),
                      ReplacementTransform(VGroup(rnd, whatever), exp))
            self.wait()

        def play_exp(): 
            self.add(exp)
            self.play(GrowFromPoint(VGroup(out_line, outs), point=rot_point, point_color=BLACK))
            self.wait()
            self.play(ReplacementTransform(exp, Coin_Q))
            self.wait()
            mid_line = deepcopy(out_line).set_z_index(-0.6)
            H_line = deepcopy(out_line).stretch_to_fit_height(np.sqrt(4+out_line.height**2)).move_to(rot_point, aligned_edge=UP).rotate(-np.arctan(2/out_line.height), about_point=rot_point)
            T_line = deepcopy(out_line).stretch_to_fit_height(np.sqrt(4+out_line.height**2)).move_to(rot_point, aligned_edge=UP).rotate(np.arctan(2/out_line.height), about_point=rot_point)
            self.play(ReplacementTransform(deepcopy(outs), TCoin[0]), GrowFromPoint(TCoin[1], ORIGIN), ReplacementTransform(deepcopy(out_line), T_line),
                      ReplacementTransform(outs, HCoin[0]), GrowFromPoint(HCoin[1], ORIGIN), ReplacementTransform(out_line, H_line))
            self.wait()
            self.play(GrowFromEdge(mid_line, UP, GR_G), GrowFromPoint(ECoin, rot_point))
            self.play(Rotate(ECoin, PI/2, UP))
            self.wait()
            meteor = VideoMobject("meteor.mp4").scale(0.12).move_to([0.8, 0.25, 0]).set_z_index(-1)
            self.play(FadeIn(meteor, target_position=[2.5, 5, 0]), rate_func=rate_functions.linear, run_time=1.5)
            meteor.speed = 0
            self.wait()
            ECoin.set_z_index(-0.6)
            self.play(LaggedStart(AnimationGroup(Group(ECoin, meteor).animate.move_to(rot_point).scale(0), mid_line.animate.scale(0).move_to(rot_point, aligned_edge=UP)), FadeIn(fade_rect), lag_ratio=0.8))
            self.wait()

        def play_outs():
            self.add(Coin_Q.set_z_index(1), HCoin, TCoin, H_line, T_line)
            orig_line = deepcopy(out_line)
            self.play(Group(HCoin, TCoin, H_line, T_line).animate.scale(0).move_to(rot_point))
            self.wait()
            self.play(GrowFromEdge(aln_right, DL), GrowFromEdge(aln_left, DR))
            self.wait()
            dice_lines = VGroup()
            nums = VGroup()
            for i in range(9):
                dice_lines.add(BranchLine(6-1.5*i))
                if i<8:
                    nums.add(TexGen(rf'{i+1}', font_sz=100, col=YELL_G).move_to([-6+1.5*i, 0, 0]))
                else:
                    nums.add(TexGen(r'$\ldots$', font_sz=100, col=YELL_G).move_to([-6+1.5*i, 0, 0]).align_to(nums[7], DOWN))
            self.play(GrowFromPoint(VGroup(dice_lines[0], nums[0]), rot_point))
            self.wait()
            self.play(LaggedStart((GrowFromPoint(VGroup(dice_lines[i+1], nums[i+1]), rot_point) for i in range(8)), lag_ratio=0.3))
            self.wait()
            self.play(Group(dice_lines, nums).animate.scale(0).move_to(rot_point), aln_left.animate.scale(0).move_to(aln_left, aligned_edge=DR), aln_right.animate.scale(0).move_to(aln_right, aligned_edge=DL))
            self.wait()
            self.play(LaggedStart(Coin_Q[1].animate.scale(0.5).shift(0.3*DOWN), GrowFromPoint(clock, Coin_Q.get_center()), lag_ratio=0.6))
            self.wait()
            num_line = RoundedRectangle(0.02, width=4, height=0.04).set_color(YELL_G).set_fill(YELL_G, opacity=1).set_stroke(YELL_G)    
            trig = Triangle().set_color(GR_G).set_fill(GR_G, opacity=1).set_stroke(GR_G).stretch_to_fit_height(2).stretch_to_fit_width(3.9).move_to(rot_point, aligned_edge=UP)
            zero = TexGen(r'0', isMath=True, font_sz=100, col=YELL_G).move_to([-2, -0.5, 0])
            inf = TexGen(r'\infty', isMath=True, font_sz=100, col=YELL_G).move_to([2, -0.5, 0])
            self.play(GrowFromPoint(VGroup(trig, num_line, zero, inf), rot_point))
            self.wait()
            self.play(VGroup(zero, inf, num_line, trig).animate.scale(0).move_to(rot_point, aligned_edge=UP))
            self.play(ReplacementTransform(VGroup(Coin_Q, clock), exp))
            self.wait()
            self.play(GrowFromPoint(VGroup(orig_line, outs), point=rot_point, point_color=BLACK))
            self.wait()
            events = TexGen(r'Events', font_sz=100, col=YELL_G).to_edge(DOWN, buff=1)
            event_line = deepcopy(orig_line).move_to([0, -2, 0], aligned_edge=DOWN)
            self.play(GrowFromPoint(VGroup(event_line, events), point=event_line.get_edge_center(UP), point_color=BLACK))
            self.wait()
            self.play(LaggedStart(Group(event_line, events).animate.scale(0).move_to(event_line.get_edge_center(UP), aligned_edge=UP),
                                  Group(outs, orig_line).animate.scale(0).move_to(rot_point, aligned_edge=UP), lag_ratio=0.7))
            self.play(ReplacementTransform(exp, Dice_Q))
            self.wait()
            dice_lines = VGroup() #buggy
            for d in Ds: #buggy
                dice_lines.add(BranchLine(d.get_x()))
            self.play(GrowFromPoint(Group(dice_lines, Ds), rot_point))
            self.wait()
        
        def play_events():
            self.add(Dice_Q, dice_lines, Ds)
            p0 = TexGen(r'P(\phantom{|})', isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            p1 = TexGen(r'P(\phantom{\textup{Event}})', isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            e1 = TexGen(r'Event', font_sz=100, col=YELL_G).move_to(p1).shift(0.42*RIGHT+0.1*UP)
            p2 = TexGen(r"P(\phantom{\textup{''rolling a 4``}})", isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            e2 = TexGen(r"''rolling a 4``", font_sz=100, col=YELL_G).move_to(p2).shift(0.42*RIGHT)
            p3 = TexGen(r"P(\phantom{\textup{''rolling an odd number``}})", isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            e3 = TexGen(r"''rolling an odd number``", font_sz=100, col=YELL_G).move_to(p2).shift(0.42*RIGHT)
            p2_cp = deepcopy(p2)
            e2_cp = deepcopy(e2)
            self.play(GrowFromCenter(p0))
            self.wait()
            self.play(ReplacementTransform(p0, p2), GrowFromCenter(e2))
            self.wait()
            l1 = deepcopy(dice_lines[2]).set_z_index(1).set_color(RYEBLUE_G).set_stroke(RYEBLUE_G).set_fill(RYEBLUE_G)
            l2 = deepcopy(dice_lines[1]).set_z_index(1).set_color(RYEBLUE_G).set_stroke(RYEBLUE_G).set_fill(RYEBLUE_G)
            l3 = deepcopy(dice_lines[3]).set_z_index(1).set_color(RYEBLUE_G).set_stroke(RYEBLUE_G).set_fill(RYEBLUE_G)
            l4 = deepcopy(dice_lines[5]).set_z_index(1).set_color(RYEBLUE_G).set_stroke(RYEBLUE_G).set_fill(RYEBLUE_G)
            l1_cp = deepcopy(l1)
            l2_cp = deepcopy(l2)
            l3_cp = deepcopy(l3)
            l4_cp = deepcopy(l4)
            Ds_cp = deepcopy(Ds)
            self.play(GrowFromPoint(l1, rot_point))
            self.wait()
            self.play(ReplacementTransform(p2, p3), ReplacementTransform(e2, e3), l1.animate.scale(0).move_to(rot_point, aligned_edge=UL))
            self.play(GrowFromPoint(Group(l2, l3, l4), rot_point))
            self.wait()
            self.play(Group(l2, l3, l4).animate.scale(0).move_to(rot_point), ReplacementTransform(p3, p1), ReplacementTransform(e3, e1))
            self.wait()
            self.play(GrowFromPoint(l1_cp, rot_point), ReplacementTransform(p1, p2_cp), ReplacementTransform(e1, e2_cp))
            self.wait()
            self.play(e2_cp.animate.set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1])))
            self.wait()
            p_four = TexGen(r'P(\phantom{\textup{Ev}})', isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            p2_four = TexGen(r'P(\phantom{4})', isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            D_four = deepcopy(Ds[3]).move_to(p_four).shift(0.42*RIGHT)
            self.play(ReplacementTransform(e2_cp, D_four), ReplacementTransform(p2_cp, p_four))
            self.wait()
            self.play(D_four[0].animate.set_color(RRED_G).set_stroke(RRED_G).set_fill(RRED_G))
            self.wait()
            nums = VGroup(TexGen(rf'{i+1}', font_sz=100, col=YELL_G, isMath=True).move_to(Ds[i]) for i in range(6))
            four = deepcopy(nums[3]).move_to(p2_four).shift(0.42*RIGHT+0.1*UP)
            self.play(ReplacementTransform(Ds, nums), ReplacementTransform(p_four, p2_four), ReplacementTransform(D_four, four))
            self.wait()
            p_odd = TexGen(r'P(\phantom{1, 3, 5})', isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            odd_nums = TexGen(r'1, 3, 5', isMath=True, font_sz=100, col=YELL_G).move_to(p_odd).shift(0.42*RIGHT)
            self.play(GrowFromPoint(Group(l2_cp, l3_cp, l4_cp), rot_point), l1_cp.animate.scale(0).move_to(rot_point, aligned_edge=UL))
            self.wait()
            self.play(ReplacementTransform(p2_four, p_odd), ReplacementTransform(four, odd_nums))
            self.wait()
            self.play(odd_nums.animate.set_color(RED_G).set_stroke(color=average_color(RED_G[0], RED_G[-1])))
            self.wait()
            self.play(ReplacementTransform(nums, Ds_cp), Group(l2_cp, l3_cp, l4_cp).animate.scale(0).move_to(rot_point), FadeOut(odd_nums))
            self.wait()
            self.play(ReplacementTransform(p_odd, p_set), Draw(e_set))
            self.wait()
            self.play(Draw(Omega_D[0:][::2]))
            self.play(LaggedStart(dice_lines.animate.scale(0).move_to(rot_point), FadeOut(Dice_Q), lag_ratio=0.4))
            self.wait()
            self.play(VGroup(Omega_D[0:][::2], Ds_cp).animate.scale_to_fit_height(1.4*Omega.height).move_to(O[1]))
            self.play(Draw(Omega))
            self.wait()

        def play_set():
            self.add(O, p_set, e_set)
            self.wait()
            p_odd = TexGen(r'P(\phantom{|||1, 3, 5||})', isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            p_4 = TexGen(r'P(\phantom{||4||})', isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
            e_odd = SetGen([Dice(1), Dice(3), Dice(5)], col=YELL_G).scale_to_fit_height(1.4*Omega.height).move_to(p_odd).shift(0.42*RIGHT)
            e_4 = SetGen([Dice(4)], col=YELL_G).scale_to_fit_height(1.4*Omega.height).move_to(p_4).shift(0.42*RIGHT)
            self.play(FadeOut(e_set), ReplacementTransform(p_set, p_odd))
            self.play(LaggedStart(FadeIn(e_odd[1], target_position=O[1][1]), FadeIn(e_odd[3], target_position=O[1][5]), FadeIn(e_odd[5], target_position=O[1][9]), lag_ratio=0.3))
            self.play(Draw(e_odd[0:][::2]))
            self.wait()
            self.play(FadeOut(e_odd[1:-1]))
            self.play(LaggedStart(FadeIn(e_4[1], target_position=O[1][7]), AnimationGroup(ReplacementTransform(p_odd, p_4), e_odd[0].animate.move_to(e_4[0]), e_odd[-1].animate.move_to(e_4[-1])), lag_ratio=0.1))
            self.wait()
            self.play(FadeOut(p_4, e_4[1], e_odd[0], e_odd[-1]))
            S = [Dice(i).scale_to_fit_height(e_odd[3].height) for i in range(1, 7)]
            power_list_1 = PowerSet(S, n_elements=1)
            power_list_2 = PowerSet(S, n_elements=2)
            power_list_3 = PowerSet(S, n_elements=3)
            power_list_4 = PowerSet(S, n_elements=4)
            power_list_5 = PowerSet(S, n_elements=5)
            subset_1s = VGroup(SetGen(deepcopy(power_list_1[0]), col=YELL_G)).next_to(O, DOWN).shift(DOWN).align_to(O[1], LEFT)
            subset_2s = VGroup(SetGen(deepcopy(power_list_2[0]), col=YELL_G)).next_to(subset_1s, RIGHT)
            subset_3s = VGroup(SetGen(deepcopy(power_list_3[0]), col=YELL_G)).next_to(subset_2s, RIGHT)
            subset_4s = VGroup(SetGen(deepcopy(power_list_4[0]), col=YELL_G)).next_to(subset_3s, RIGHT)
            subset_5s = VGroup(SetGen(deepcopy(power_list_5[0]), col=YELL_G)).next_to(subset_4s, RIGHT)
            subset_6s = deepcopy(O[1]).next_to(subset_5s, RIGHT)
            Omega2 = TexGen(r'\Omega', isMath=True, font_sz=100, col=YELL_G).move_to(subset_6s, aligned_edge=LEFT)
            for l in power_list_1[1:]:
                subset_1s.add(SetGen(deepcopy(l), col=YELL_G).next_to(subset_1s[-1], DOWN))
            for l in power_list_2[1:]:
                subset_2s.add(SetGen(deepcopy(l), col=YELL_G).next_to(subset_2s[-1], DOWN))
            for l in power_list_3[1:]:
                subset_3s.add(SetGen(deepcopy(l), col=YELL_G).next_to(subset_3s[-1], DOWN))
            for l in power_list_4[1:]:
                subset_4s.add(SetGen(deepcopy(l), col=YELL_G).next_to(subset_4s[-1], DOWN))
            for l in power_list_5[1:]:
                subset_5s.add(SetGen(deepcopy(l), col=YELL_G).next_to(subset_5s[-1], DOWN))
            empty_set = TexGen(r'\{ \}', isMath=True, col=YELL_G, font_sz=100).scale_to_fit_height(subset_1s[0].height).next_to(O, DOWN).shift(DOWN).align_to(O[1], LEFT)
            CAM = self.camera.frame
            CAM.save_state()
            self.play(LaggedStart(*(GrowFromCenter(s) for s in subset_1s)), CAM.animate.scale(1.4).move_to(CAM, aligned_edge=UP), run_time=1.5)
            self.wait()
            self.play(LaggedStart(*(GrowFromCenter(s) for s in subset_2s)), CAM.animate.scale(2.04).move_to(CAM, aligned_edge=UP), run_time=1.5)
            self.wait()
            self.play(LaggedStart(*(GrowFromCenter(s) for s in subset_3s)), CAM.animate.scale(1.3).move_to(CAM, aligned_edge=UP), run_time=1.5)
            self.wait()
            self.play(LaggedStart(*(GrowFromCenter(s) for s in subset_4s)), CAM.animate.shift(3*RIGHT), run_time=1.5)
            self.wait()
            self.play(LaggedStart(*(GrowFromCenter(s) for s in subset_5s)), CAM.animate.shift(3*RIGHT), run_time=1.5)
            self.wait()
            self.play(GrowFromCenter(subset_6s), CAM.animate.shift(3*RIGHT), run_time=1)
            self.wait()
            self.play(ReplacementTransform(subset_6s, Omega2))
            self.wait()
            self.play(LaggedStart(VGroup(subset_1s, subset_2s, subset_3s, subset_4s, subset_5s, Omega2).animate.next_to(empty_set, RIGHT, aligned_edge=UP), GrowFromCenter(empty_set)))
            self.wait()
            power_brackets = TexGen(r'\{\phantom{|||}\}', isMath=True, font_sz=1000, col=YELL_G, stroke_w=0.01).scale_to_fit_height(subset_3s.height).move_to(VGroup(empty_set, subset_1s, subset_2s, subset_3s, subset_4s, subset_5s, Omega2))
            power_set = TexGen(r'\mathcal{P}(\Omega)', isMath=True, font_sz=1600, col=YELL_G).move_to(VGroup(empty_set, subset_1s, subset_2s, subset_3s, subset_4s, subset_5s, Omega2))
            self.play(Draw(power_brackets))
            self.wait()
            scl = 1.17
            s_e_4 = deepcopy(subset_1s[3]).scale(scl)
            s_e_odd = deepcopy(subset_3s[5]).scale(scl)
            s_e_sm5 = deepcopy(subset_4s[0]).scale(scl)
            s_e_even = deepcopy(subset_3s[14]).scale(scl)
            s_e_both = deepcopy(subset_2s[6]).scale(scl)
            p_set_group = deepcopy(VGroup(power_brackets, empty_set, subset_1s, subset_2s, subset_3s, subset_4s, subset_5s, Omega2))
            self.play(VGroup(power_brackets, empty_set, Omega2).animate.set_color(GR_G).set_stroke(GR_G),
                      *(s1[1:][::2][0][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s1 in subset_1s),
                      *(s2[1:][::2][0][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s2 in subset_2s),
                      *(s2[1:][::2][1][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s2 in subset_2s),
                      *(s3[1:][::2][0][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s3 in subset_3s),
                      *(s3[1:][::2][1][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s3 in subset_3s),
                      *(s3[1:][::2][2][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s3 in subset_3s),
                      *(s4[1:][::2][0][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s4 in subset_4s),
                      *(s4[1:][::2][1][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s4 in subset_4s),
                      *(s4[1:][::2][2][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s4 in subset_4s),
                      *(s4[1:][::2][3][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s4 in subset_4s),
                      *(s5[1:][::2][0][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s5 in subset_5s),
                      *(s5[1:][::2][1][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s5 in subset_5s),
                      *(s5[1:][::2][2][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s5 in subset_5s),
                      *(s5[1:][::2][3][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s5 in subset_5s),
                      *(s5[1:][::2][4][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for s5 in subset_5s),
                      *(s[0:][::2].animate.set_color(GR_G).set_stroke(average_color(GR_G[0], GR_G[-1])) for s in subset_1s),
                      *(s[0:][::2].animate.set_color(GR_G).set_stroke(average_color(GR_G[0], GR_G[-1])) for s in subset_2s),
                      *(s[0:][::2].animate.set_color(GR_G).set_stroke(average_color(GR_G[0], GR_G[-1])) for s in subset_3s),
                      *(s[0:][::2].animate.set_color(GR_G).set_stroke(average_color(GR_G[0], GR_G[-1])) for s in subset_4s),
                      *(s[0:][::2].animate.set_color(GR_G).set_stroke(average_color(GR_G[0], GR_G[-1])) for s in subset_5s))
            self.wait()
            subset_1s[3].save_state()
            subset_3s[5].save_state()
            subset_4s[0].save_state()
            subset_3s[14].save_state()
            subset_2s[6].save_state()
            Omega2.save_state()
            empty_set.save_state()
            self.play(subset_1s[3].animate.become(s_e_4))
            self.wait()
            self.play(Restore(subset_1s[3]))
            self.play(subset_3s[5].animate.become(s_e_odd))
            self.wait()
            self.play(Restore(subset_3s[5]))
            self.play(subset_4s[0].animate.become(s_e_sm5))
            self.wait()
            self.play(subset_3s[14].animate.become(s_e_even))
            self.wait()
            self.play(subset_2s[6].animate.become(s_e_both), deepcopy(s_e_even).animate.move_to(s_e_both).fade(darkness=1),
                      deepcopy(s_e_sm5).animate.move_to(s_e_both).fade(darkness=1), Restore(subset_4s[0]), Restore(subset_3s[14]))
            self.wait()
            self.play(Restore(subset_2s[6]))
            self.play(Omega2.animate.scale(scl+0.1).set_color(YELL_G).set_stroke(average_color(YELL_G[0], YELL_G[-1])))
            self.wait()
            self.play(Restore(Omega2))
            self.play(empty_set.animate.scale(scl+0.1).set_color(YELL_G).set_stroke(average_color(YELL_G[0], YELL_G[-1])))
            self.wait()
            self.play(Restore(empty_set))
            self.wait()
            self.play(ReplacementTransform(VGroup(power_brackets, empty_set, subset_1s, subset_2s, subset_3s, subset_4s, subset_5s, Omega2), p_set_group))
            self.wait()
            self.play(ReplacementTransform(p_set_group, power_set))
            self.wait()
            p_func = TexGen(r'P: \phantom{\mathcal{P}(\Omega)} \to [0, 1]', isMath=True, font_sz=100, col=YEBLUE_G)
            self.play(Restore(CAM), power_set.animate.scale_to_fit_height(p_func.height).move_to(p_func).shift(LEFT), run_time=1.5)
            self.play(Draw(p_func))
            E = TexGen(r'E', isMath=True, font_sz=100, col=YELL_G).next_to(power_set, DOWN).shift(0.5*DOWN).align_to(power_set, RIGHT)
            mapsTo = TexGen(r'\mapsto', font_sz=100, col=YEBLUE_G, isMath=True).next_to(E, RIGHT, buff=0.43)
            p = TexGen(r'P(\phantom{E})', isMath=True, font_sz=100, col=YEBLUE_G)
            E2 = deepcopy(E).move_to(p).shift(0.42*RIGHT+0.1*UP)
            p_E = VGroup(p, E2).next_to(mapsTo, RIGHT).shift(0.12*DOWN).shift(0.1*RIGHT)
            self.wait()
            self.play(FadeIn(E, target_position=power_set))
            self.play(GrowFromEdge(mapsTo, LEFT))
            self.play(GrowFromEdge(p_E, LEFT))
            self.wait()
            a = TexGen(r'a', font_sz=100, col=YEBLUE_G).next_to(measure, RIGHT, aligned_edge=DOWN, buff=0.4)
            st = TexGen(r'Set', font_sz=100, col=YELL_G).next_to(a, RIGHT, aligned_edge=DOWN, buff=0.4)
            q = TexGen(r'\phantom{S}?', font_sz=100, col=YEBLUE_G).next_to(st, RIGHT, aligned_edge=DOWN, buff=0.1)
            measure_a_set = VGroup(measure, a, st, q)
            self.play(FadeOut(O, p_func, E, mapsTo, power_set))
            self.play(Draw(measure_a_set))
            self.wait()
            self.play(FadeOut(p_E), ReplacementTransform(VGroup(a, st, q), theory))
            self.wait()

        def play_measure():
            self.add(measure, theory)
            m = TexGen(r'\mu', font_sz=115, col=YEBLUE_G, isMath=True).move_to(measure).shift(0.1*DOWN)
            eq = TexGen(r'=', font_sz=110, col=YEBLUE_G).move_to([-0.3, m.get_y()+0.2, 0])
            length = TexGen(r'Length', font_sz=100, col=YEBLUE_G).next_to(eq, RIGHT, buff=0.6)
            length_cp = deepcopy(length)
            area = TexGen(r'Area', font_sz=100, col=YEBLUE_G).next_to(eq, RIGHT, buff=0.6).align_to(length, UP)
            volume = TexGen(r'Volume', font_sz=100, col=YEBLUE_G).next_to(eq, RIGHT, buff=0.6).align_to(length, UP)
            volume_cp = deepcopy(volume)
            brk = TexGen(r'(\phantom{||||})', font_sz=110, col=YEBLUE_G, isMath=True).next_to(eq, LEFT, buff=0.6)
            l1 = Line(ORIGIN, [1, 0, 0]).set_color(YELL_G).set_stroke(width=6, color=YELL_G).move_to(brk).set_z_index(1)
            tick_buff=0.0000000000000000000000000000000000000000000001
            x_len = 3-tick_buff
            x_ax = NumberLine(x_range=[0, x_len], unit_size=1, length=x_len, include_tip=True, tip_shape=StealthTip, tip_height=0.3, include_ticks=False).shift(x_len/2*RIGHT).set_stroke(color=GR_G, width=5).set_fill(GR_G)
            y_ax = deepcopy(x_ax).rotate(PI/2, about_point=ORIGIN)
            z_ax = deepcopy(x_ax).rotate(-PI/2, about_point=ORIGIN, axis=UP)
            tick_sz = 0.2
            x_ticks = VGroup(Line(ORIGIN, [0, tick_sz, 0]).set_stroke(GR_G, width=5).move_to(x_ax.n2p(1)), Line(ORIGIN, [0, tick_sz, 0]).set_stroke(GR_G, width=5).move_to(x_ax.n2p(2)))
            y_ticks = VGroup(Line(ORIGIN, [tick_sz, 0, 0]).set_stroke(GR_G, width=5).move_to(y_ax.n2p(1)), Line(ORIGIN, [tick_sz, 0, 0]).set_stroke(GR_G, width=5).move_to(y_ax.n2p(2)))
            ax = VGroup(x_ax, y_ax, z_ax, x_ticks, y_ticks).move_to(ORIGIN, aligned_edge=DL)
            xy_plane = NumberPlane(x_range=[0, x_len], y_range=[0, x_len], x_length=x_len, y_length=x_len).move_to(ax, aligned_edge=UP+RIGHT+IN).set_stroke(GR_G).set_z_index(-1)
            cube_down = Cube(1, fill_color=YELL_G, fill_opacity=1).set_color(YELL_G).set_stroke(width=1, color=YEW_G).move_to(xy_plane).shift(x_len/2*OUT).set_z_index(2).rotate(-0.1*PI, axis=UP+LEFT)
            cube_up = deepcopy(cube_down).move_to(brk)
            cube_up_cp = deepcopy(cube_up)
            VGroup(ax, cube_down).move_to(l1).shift(0.073*DOWN+0.076*LEFT)
            sq = Square(1).set_color(YELL_G).set_stroke(YELL_G, width=0).set_fill(YELL_G, opacity=1).shift(2*(RIGHT+UP+OUT))
            self.play(FadeOut(theory))
            self.play(ReplacementTransform(measure, m)) 
            self.wait()
            self.play(LaggedStart(GrowFromEdge(brk, RIGHT), m.animate.next_to(brk, LEFT).shift(0.2*DOWN), lag_ratio=0.02))
            self.wait()
            l2 = FunctionGraph(lambda x: 0.6*np.sin(x), x_range=[-1.2*PI, 1.2*PI]).scale_to_fit_width(l1.width).set_color(YELL_G).set_stroke(YELL_G, width=6).move_to(l1)
            l1_cp = deepcopy(l1)
            l1_cp2 = deepcopy(l1)
            l2_cp = deepcopy(l2)
            self.play(Create(l1))
            self.wait()
            self.play(Draw(eq))
            self.wait()
            self.play(Draw(length))
            self.wait()
            sq = Square(1).set_color(YELL_G).set_stroke(YELL_G, width=0).set_fill(YELL_G, opacity=1).move_to(brk)
            sq_cp = deepcopy(sq)
            sq_cp2 = deepcopy(sq)
            self.play(l1.animate.become(l2))
            self.wait()
            self.play(l1.animate.become(sq), ReplacementTransform(length, area))
            self.wait()
            self.play(l1.animate.become(cube_up), ReplacementTransform(area, volume))
            self.wait()
            self.play(l1.animate.become(l1_cp), ReplacementTransform(volume, length_cp))
            self.wait()
            a = TexGen(r'a', isMath=True, col=GR_G).next_to(x_ticks[0], DOWN)
            b = TexGen(r'b', isMath=True, col=GR_G).next_to(x_ticks[1], DOWN).align_to(a, DOWN)
            c = TexGen(r'c', isMath=True, col=GR_G).next_to(y_ticks[0], LEFT)
            d = TexGen(r'd', isMath=True, col=GR_G).next_to(y_ticks[1], LEFT)
            a.save_state()
            b.save_state()
            x_ax.save_state()
            x_ticks.save_state()
            VGroup(x_ax, x_ticks, a, b).shift(x_len/2*UP)
            set_line = TexGen(r'\{x \in \mathbb{R} \mid a \leq x \leq b\}', isMath=True, col=YELL_G).next_to(l1_cp, UP).shift(0.7*UP)
            interval = TexGen(r'[a, b]', isMath=True, col=YELL_G).move_to(set_line, aligned_edge=UP)
            set_func = TexGen(r'f(x)', isMath=True, col=YELL_G).next_to(l2_cp, UR, buff=0.6)
            set_sq = TexGen(r'[a, b] \times [c, d]', isMath=True, col=YELL_G).move_to(set_func, aligned_edge=LEFT)
            self.play(FadeOut(m, brk, eq, length_cp))
            self.play(LaggedStart(Create(x_ax), AnimationGroup(GrowFromCenter(x_ticks[0]), GrowFromCenter(x_ticks[1]), GrowFromPoint(a, x_ticks[0]), GrowFromPoint(b, x_ticks[1])), lag_ratio=0.6))
            self.play(GrowFromPoint(set_line, l1_cp.get_center()))
            self.wait()
            self.play(ReplacementTransform(set_line, interval))
            self.wait()
            self.play(l1.animate.become(l2_cp.move_to(l1)), FadeOut(interval))
            self.wait()
            self.play(GrowFromCenter(y_ax), Restore(x_ax), Restore(x_ticks), Restore(a), Restore(b))
            self.play(GrowFromPoint(set_func, l2_cp.get_center()))
            self.wait()
            self.play(ReplacementTransform(set_func, set_sq), l1.animate.become(sq_cp.move_to(l1).shift(x_len/2*IN)), GrowFromCenter(y_ticks[0]), GrowFromCenter(y_ticks[1]), GrowFromPoint(c, y_ticks[0]), GrowFromPoint(d, y_ticks[1]))
            self.wait()
            self.play(LaggedStart(Rotate(set_sq, -0.1*PI, axis=UP+LEFT, run_time=1.5), Rotate(VGroup(ax, l1, a, b, c, d), -0.1*PI, axis=UP+LEFT), lag_ratio=0.3))
            set_cube = TexGen(r'[a, b] \times [c, d] \times [e, f]', isMath=True, col=YELL_G).move_to(set_sq, aligned_edge=LEFT).rotate(-0.1*PI, axis=UP+LEFT)
            z_ticks = VGroup(Line(ORIGIN, [0, tick_sz, 0]).set_stroke(GR_G, width=5).move_to(z_ax.n2p(1)), Line(ORIGIN, [0, tick_sz, 0]).set_stroke(GR_G, width=5).move_to(z_ax.n2p(2)))
            e = TexGen(r'e', isMath=True, col=GR_G).next_to(z_ticks[0], DOWN).rotate(-0.1*PI, axis=UP+LEFT)
            f = TexGen(r'f', isMath=True, col=GR_G).next_to(z_ticks[1], DOWN).rotate(-0.1*PI, axis=UP+LEFT)
            self.play(ReplacementTransform(set_sq, set_cube), l1.animate.become(cube_down), GrowFromCenter(z_ticks[0]), GrowFromCenter(z_ticks[1]), GrowFromPoint(e, z_ticks[0]), GrowFromPoint(f, z_ticks[1]))
            self.wait()
            self.play(FadeOut(ax, a, b, c, d, e, f, z_ticks))
            brk2 = TexGen(r'(\phantom{|||||})', font_sz=110, col=YEBLUE_G, isMath=True).next_to(eq, LEFT, buff=0.6)
            m.next_to(brk2, LEFT).shift(0.2*DOWN)
            s = TexGen(r'Set', col=YELL_G, font_sz=100).move_to(brk2)
            s_cp = deepcopy(s)
            size = TexGen(r"''Size``", font_sz=100, col=YEBLUE_G).next_to(eq, RIGHT, buff=0.6).align_to(length, UP)
            content = TexGen(r"''Content``", font_sz=100, col=YEBLUE_G).next_to(eq, RIGHT, buff=0.6).align_to(length, UP)
            self.play(FadeIn(m, brk2), ReplacementTransform(VGroup(l1, set_cube), s))
            self.wait()
            self.play(Draw(eq))
            self.play(Draw(size))
            self.wait()
            self.play(ReplacementTransform(size, content))
            self.wait()
            self.play(ReplacementTransform(content, volume_cp))
            self.wait()
            self.play(ReplacementTransform(brk2, brk), m.animate.next_to(brk, LEFT).shift(0.2*DOWN), s.animate.become(cube_up_cp))
            self.wait()
            oneD = TexGen(r"1D", font_sz=100, col=GR_G).next_to(volume_cp, UP).shift(0.3*UP)
            twoD = TexGen(r"2D", font_sz=100, col=GR_G).next_to(volume_cp, UP).shift(0.3*UP)
            abstract = TexGen(r"abstract", font_sz=100, col=GR_G).next_to(volume_cp, UP).shift(0.3*UP)
            self.play(s.animate.become(sq_cp2))
            self.play(Draw(twoD))
            self.wait()
            self.play(ReplacementTransform(twoD, oneD), s.animate.become(l1_cp2))
            self.wait()
            e = TexGen(r'E', col=YELL_G, font_sz=110, isMath=True).move_to(brk).align_to(s_cp, DOWN)
            self.play(s.animate.become(e), oneD.animate.become(abstract))
            self.wait()
            self.play(FadeOut(oneD, s, eq, brk, volume_cp))
            self.play(m.animate.to_edge(UP).to_edge(LEFT, buff=0.8))
            self.wait()

        def play_rules():
            measurable = TexGen(r'measurable', col=YEBLUE_G).next_to(r1, DOWN)
            non = TexGen(r'non-negative', col=YEBLUE_G).next_to(r2, DOWN).align_to(measurable, UP)
            addi = TexGen(r'additive', col=YEBLUE_G).next_to(r3, DOWN).align_to(measurable, UP)
            room = Cube(1, fill_color=YELL_G, fill_opacity=0.8).set_color(YELL_G).set_stroke(width=1, color=BLACK).stretch_to_fit_width(1.3).rotate(-0.13*PI, axis=UP+LEFT).next_to(measurable, DOWN).shift(0.5*DOWN)
            Omega.next_to(room, LEFT, buff=0.7).set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1]))
            self.add(m)
            self.play(GrowFromPoint(VGroup(r1, r2, r3), m.get_edge_center(RIGHT)))
            self.wait()
            self.play(GrowFromPoint(measurable, r1.get_edge_center(DOWN)), r1.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G))
            self.wait()
            room[0].set_z_index(-1)
            self.play(Create(room[5]))
            self.wait()
            self.play(room[5].animate.set_color(GR_G).set_stroke(width=1, color=BLACK), Create(room[0]), run_time=0.5)
            self.play(room[0].animate.set_color(GR_G).set_stroke(width=1, color=BLACK), Create(room[2]), run_time=0.5)
            self.play(room[2].animate.set_color(GR_G).set_stroke(width=1, color=BLACK), Create(room[3]), run_time=0.5)
            self.play(room[3].animate.set_color(GR_G).set_stroke(width=1, color=BLACK), Create(room[1]), run_time=0.5)
            self.play(room[1].animate.set_color(GR_G).set_stroke(width=1, color=BLACK), Create(room[4]), run_time=0.5)
            self.play(room[4].animate.set_color(GR_G).set_stroke(width=1, color=BLACK))
            self.wait()
            self.play(Draw(Omega))
            self.wait()
            self.play(room[3].animate.set_color(YELL_G).set_stroke(width=1, color=BLACK))
            room[3].save_state()
            dist = 0.3
            self.wait()
            self.play(room[3].animate.shift(dist*RIGHT))
            self.wait()
            self.play(Restore(room[3]))
            self.play(room[4].animate.set_color(YELL_G).set_stroke(width=1, color=BLACK))
            self.wait()
            self.play(VGroup(room[3], room[4]).animate.shift(dist*UR))
            self.wait()
            self.play(VGroup(room[3], room[4]).animate.shift(dist*DL))
            self.play(room[3].animate.set_color(GR_G).set_stroke(width=1, color=BLACK),
                      room[4].animate.set_color(GR_G).set_stroke(width=1, color=BLACK))
            self.wait()
            self.play(room[5].animate.shift(dist*DOWN),
                      room[0].animate.shift(dist*IN),
                      room[2].animate.shift(dist*LEFT),
                      room[3].animate.shift(dist*RIGHT),
                      room[1].animate.shift(dist*OUT),
                      room[4].animate.shift(dist*UP))
            self.wait()
            self.play(room[5].animate.shift(dist*UP),
                      room[0].animate.shift(dist*OUT),
                      room[2].animate.shift(dist*RIGHT),
                      room[3].animate.shift(dist*LEFT),
                      room[1].animate.shift(dist*IN),
                      room[4].animate.shift(dist*DOWN))
            self.wait()
            power_set = TexGen(r'\mathcal{P}(\Omega)', isMath=True, font_sz=100, col=YELL_G).next_to(room, DOWN).shift(0.5*DOWN)
            m_func = TexGen(r'\mu:', font_sz=115, col=YEBLUE_G, isMath=True).next_to(power_set, LEFT, buff=0.4).shift(0.1*DOWN)
            to = TexGen(r'\to', isMath=True, font_sz=100, col=YEBLUE_G).next_to(power_set, RIGHT, buff=0.4)
            pos_i = TexGen(r'[0, \infty]', isMath=True, font_sz=100, col=YEBLUE_G).next_to(to, RIGHT, buff=0.4)
            self.play(LaggedStart(AnimationGroup(LaggedStart(*(deepcopy(room[0]).animate.move_to(power_set.get_edge_center(UP)).set_color(YELL_G).set_stroke(width=1, color=BLACK).scale(0) for i in range(20))),
                      LaggedStart(*(deepcopy(room[1]).animate.move_to(power_set.get_edge_center(UP)).set_color(YELL_G).set_stroke(width=1, color=BLACK).scale(0) for i in range(20))),
                      LaggedStart(*(deepcopy(room[2]).animate.move_to(power_set.get_edge_center(UP)).set_color(YELL_G).set_stroke(width=1, color=BLACK).scale(0) for i in range(20))),
                      LaggedStart(*(deepcopy(room[3]).animate.move_to(power_set.get_edge_center(UP)).set_color(YELL_G).set_stroke(width=1, color=BLACK).scale(0) for i in range(20))),
                      LaggedStart(*(deepcopy(room[4]).animate.move_to(power_set.get_edge_center(UP)).set_color(YELL_G).set_stroke(width=1, color=BLACK).scale(0) for i in range(20))),
                      LaggedStart(*(deepcopy(room[5]).animate.move_to(power_set.get_edge_center(UP)).set_color(YELL_G).set_stroke(width=1, color=BLACK).scale(0) for i in range(20)))),
                      GrowFromEdge(power_set.set_z_index(1), UP), lag_ratio=0.4), run_time=3)
            self.wait()
            self.play(Draw(m_func))
            self.wait()
            self.play(GrowFromEdge(to, LEFT))
            self.wait()
            self.play(measurable.animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])),
                      r1.animate.set_color(GR_G).set_stroke(GR_G), GrowFromPoint(non, r2.get_edge_center(DOWN)),
                      r2.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G))
            self.wait()
            self.play(GrowFromPoint(pos_i, non.get_edge_center(DOWN)))
            self.wait()
            empty_set = TexGen(r'\{\}', col=YELL_G, font_sz=100, isMath=True).next_to(power_set, DOWN, aligned_edge=RIGHT).shift(0.5*DOWN)
            mapsTo = TexGen(r'\mapsto', font_sz=100, col=YEBLUE_G, isMath=True).next_to(empty_set, RIGHT, buff=0.4)
            zero = TexGen(r'0', isMath=True, font_sz=100, col=YEBLUE_G).next_to(mapsTo, RIGHT, buff=0.4)
            self.play(FadeIn(empty_set, target_position=power_set))
            self.wait()
            self.play(GrowFromEdge(mapsTo, LEFT))
            self.play(GrowFromEdge(zero, LEFT))
            self.wait()
            self.play(non.animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])),
                      r2.animate.set_color(GR_G).set_stroke(GR_G), GrowFromPoint(addi, r3.get_edge_center(DOWN)),
                      r3.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G))
            self.wait()
            self.play(room[3].animate.set_color(YELL_G).set_stroke(width=1, color=BLACK),
                      room[4].animate.set_color(YELL_G).set_stroke(width=1, color=BLACK))
            self.play(FadeOut(empty_set, zero))
            sub = VGroup(deepcopy(room[4]), deepcopy(room[3])).move_to(empty_set, aligned_edge=RIGHT)
            cup = TexGen(r'\cup', font_sz=100, isMath=True, col=YELL_G).next_to(sub[1], LEFT, aligned_edge=DOWN, buff=0.1)
            self.play(FadeIn(sub, target_position=power_set))
            self.wait()
            self.play(sub[0].animate.next_to(cup, LEFT, buff=0.1, aligned_edge=UP).shift(0.2*UP))
            self.play(Draw(cup))
            self.wait()
            brk_room3 = TexGen(r'(\phantom{|})', isMath=True, font_sz=110, col=YEBLUE_G)
            m_room3 = deepcopy(m).next_to(brk_room3, LEFT).shift(0.2*DOWN)
            m_of_room3 = VGroup(m_room3, brk_room3, deepcopy(sub[1]).move_to(brk_room3))
            plus = TexGen(r'+', isMath=True, font_sz=100, col=YEBLUE_G).next_to(m_of_room3, LEFT, buff=0.3)
            brk_room4 = TexGen(r'(\phantom{||||})', isMath=True, font_sz=110, col=YEBLUE_G)
            m_room4 = deepcopy(m).next_to(brk_room4, LEFT).shift(0.2*DOWN)
            m_of_room4 = VGroup(m_room4, brk_room4, deepcopy(sub[0]).move_to(brk_room4)).next_to(plus, LEFT, buff=0.3)
            m_sum = VGroup(m_of_room3, plus, m_of_room4).next_to(mapsTo, RIGHT, buff=0.3)
            m_of_room3[2].set_y(sub[1].get_y())
            m_of_room4[2].set_y(sub[0].get_y())
            self.play(GrowFromEdge(m_sum, LEFT))
            self.wait()
            self.play(FadeOut(Omega, m_func, power_set, to, pos_i, m_sum, sub, cup, mapsTo),
                      room.animate.fade(darkness=1),
                      r1.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G), measurable.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      r2.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G), non.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.wait()
            room.set_z_index(0)
            self.play(ReplacementTransform(m, p),
                      r1.animate.set_color(GR_G).set_stroke(GR_G), measurable.animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])),
                      r2.animate.set_color(GR_G).set_stroke(GR_G), non.animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])),
                      r3.animate.set_color(GR_G).set_stroke(GR_G), addi.animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])))
            self.wait()

        def play_prob():
            measurable = TexGen(r'measurable', col=GR_G).next_to(r1, DOWN)
            non = TexGen(r'non-negative', col=GR_G).next_to(r2, DOWN).align_to(measurable, UP)
            addi = TexGen(r'additive', col=GR_G).next_to(r3, DOWN).align_to(measurable, UP)
            self.add(p, r1, r2, r3, measurable, non, addi)
            scl = 0.57
            Omega.next_to(p, DOWN, aligned_edge=LEFT).set_y(0.8)
            Omega_D.scale(scl).next_to(Omega, RIGHT, buff=0.35)
            self.play(LaggedStart(*(GrowFromCenter(d) for d in Omega_D[1:][::2])))
            self.wait()
            self.play(Draw(Omega), Draw(Omega_D[0:][::2]))
            self.wait()
            self.play(r1.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G), measurable.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.wait()
            self.play(Omega.animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])),
                      Omega_D[0:][::2].animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])),
                      *(Omega_D[1:][::2][i][0].animate.set_color(GR_G).set_stroke(GR_G).set_fill(GR_G) for i in range(6)))
            self.wait()
            p_func = TexGen(r'P:', font_sz=100, col=YEBLUE_G, isMath=True).next_to(Omega, DOWN, buff=1.2, aligned_edge=LEFT)
            power_set = TexGen(r'\mathcal{P}(\Omega)', isMath=True, font_sz=100, col=YELL_G).next_to(p_func, RIGHT, buff=0.4).shift(0.08*DOWN)
            to = TexGen(r'\to', isMath=True, font_sz=100, col=YEBLUE_G).next_to(power_set, RIGHT, buff=0.4)
            pos_i = TexGen(r'[0, 1]', isMath=True, font_sz=100, col=YEBLUE_G).next_to(to, RIGHT, buff=0.4)
            empty_set = TexGen(r'\{\}', col=YELL_G, font_sz=100, isMath=True).next_to(power_set, DOWN, aligned_edge=RIGHT).shift(0.3*DOWN)
            mapsTo = TexGen(r'\mapsto', font_sz=100, col=YEBLUE_G, isMath=True).next_to(empty_set, RIGHT, buff=0.4)
            zero = TexGen(r'0', isMath=True, font_sz=100, col=YEBLUE_G).next_to(mapsTo, RIGHT, buff=0.4)
            om = TexGen(r'\Omega', col=YELL_G, font_sz=100, isMath=True).move_to(empty_set, aligned_edge=RIGHT)
            one = TexGen(r'1', isMath=True, font_sz=100, col=YEBLUE_G).next_to(mapsTo, RIGHT, buff=0.4)
            self.play(Draw(power_set))
            self.wait()
            self.play(Draw(p_func))
            self.wait()
            self.play(measurable.animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])),
                      r1.animate.set_color(GR_G).set_stroke(GR_G), GrowFromEdge(to, LEFT),
                      r2.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G),
                      non.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.play(GrowFromEdge(pos_i, LEFT))
            self.wait()
            self.play(FadeIn(empty_set, target_position=power_set))
            self.wait()
            self.play(GrowFromEdge(mapsTo, LEFT))
            self.play(GrowFromEdge(zero, LEFT))
            self.wait()
            self.play(FadeOut(empty_set, zero))
            self.play(FadeIn(om, target_position=power_set))
            self.wait()
            self.play(GrowFromEdge(one, LEFT))
            self.wait()
            self.play(non.animate.set_color(GR_G).set_stroke(color=average_color(GR_G[0], GR_G[-1])),
                      r2.animate.set_color(GR_G).set_stroke(GR_G),
                      r3.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G),
                      addi.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])))
            self.wait()
            e_1_4 = SetGen([Dice(1), Dice(4)], col=YELL_G).scale(scl).move_to(empty_set, aligned_edge=RIGHT)
            e_1 = SetGen([Dice(1)], col=YELL_G).scale(scl)
            e_4 = SetGen([Dice(4)], col=YELL_G).scale(scl)
            brk_e = TexGen(r'(\phantom{||||})', isMath=True, font_sz=100, col=YEBLUE_G)
            p_e = deepcopy(p).next_to(brk_e, LEFT)
            p_of_e_4 = VGroup(p_e, brk_e, e_4.move_to(brk_e))
            plus = TexGen(r'+', isMath=True, font_sz=100, col=YEBLUE_G).next_to(p_of_e_4, LEFT, buff=0.3)
            p_of_e_1 = VGroup(deepcopy(p_e), deepcopy(brk_e), e_1.move_to(brk_e)).next_to(plus, LEFT, buff=0.3)
            p_sum = VGroup(p_of_e_1, plus, p_of_e_4).next_to(mapsTo, RIGHT, buff=0.3)
            self.play(FadeOut(om, one))
            self.play(FadeIn(e_1_4, target_position=power_set))
            self.wait()
            self.play(GrowFromEdge(p_sum, LEFT))
            self.wait()
            self.play(r1.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G), measurable.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      r2.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G), non.animate.set_color(YEBLUE_G).set_stroke(color=average_color(YEBLUE_G[0], YEBLUE_G[-1])),
                      FadeOut(Omega, Omega_D, p_func, power_set, to, pos_i, e_1_4, mapsTo, p_sum))
            self.wait()
            self.play(FadeOut(r1, r2, r3, measurable, non, addi))
            self.wait()

        def play_mass():
            self.add(p)
            brk = TexGen(r'(\phantom{|||})', isMath=True, font_sz=100, col=YEBLUE_G).next_to(p, RIGHT).shift(0.1*DOWN)
            empty_set = TexGen(r'\{\}', col=YELL_G, font_sz=100, isMath=True).move_to(brk)
            om = TexGen(r'\Omega', col=YELL_G, font_sz=100, isMath=True).move_to(brk).align_to(p, DOWN)
            eq = TexGen(r'=', col=YEBLUE_G, font_sz=100, isMath=True).next_to(brk, RIGHT, buff=0.44).set_y(p.get_y())
            zero = TexGen(r'0', isMath=True, font_sz=100, col=YEBLUE_G).next_to(eq, RIGHT, buff=0.4).align_to(p, UP)
            one = TexGen(r'1', isMath=True, font_sz=100, col=YEBLUE_G).next_to(eq, RIGHT, buff=0.4).align_to(p, UP)
            self.play(GrowFromEdge(VGroup(brk, empty_set), LEFT))
            self.play(GrowFromEdge(VGroup(eq, zero), LEFT))
            self.wait()
            self.play(ReplacementTransform(empty_set, om), ReplacementTransform(zero, one))
            align_sum = TexGen(r'P(\phantom{|||})+P(\phantom{|||})+P(\phantom{|||})+P(\phantom{|||})+P(\phantom{|||})+P(\phantom{|||})', isMath=True, font_sz=57, col=YEBLUE_G).move_to(p).to_edge(LEFT, buff=0.5).shift(0.05*DOWN)
            SUM = VGroup(TexGen(r'P(\phantom{|||})', isMath=True, font_sz=57, col=YEBLUE_G).move_to(align_sum, aligned_edge=LEFT))
            s_buff = 0.205
            SUM.add(TexGen(r'+', isMath=True, font_sz=57, col=YEBLUE_G).next_to(SUM[0], RIGHT, buff=s_buff))
            for i in range(2, 11, 2):
                SUM.add(VGroup(TexGen(r'P(\phantom{|||})', isMath=True, font_sz=57, col=YEBLUE_G).next_to(SUM[i-1], RIGHT, buff=s_buff)))
                SUM.add(TexGen(r'+', isMath=True, font_sz=57, col=YEBLUE_G).next_to(SUM[i], RIGHT, buff=s_buff))
            SUM = SUM[0:-1]
            self.wait()
            e_1 = SetGen([Dice(1)], col=YELL_G).scale(0.27).move_to(brk).shift(1.062*LEFT+0.073*UP)
            e_2 = SetGen([Dice(2)], col=YELL_G).scale(0.27).move_to(e_1).shift(2.134*RIGHT)
            e_3 = SetGen([Dice(3)], col=YELL_G).scale(0.27).move_to(e_2).shift(2.134*RIGHT)
            e_4 = SetGen([Dice(4)], col=YELL_G).scale(0.27).move_to(e_3).shift(2.134*RIGHT)
            e_5 = SetGen([Dice(5)], col=YELL_G).scale(0.27).move_to(e_4).shift(2.134*RIGHT)
            e_6 = SetGen([Dice(6)], col=YELL_G).scale(0.27).move_to(e_5).shift(2.134*RIGHT)
            E = VGroup(e_1, e_2, e_3, e_4, e_5, e_6)
            self.play(ReplacementTransform(VGroup(p, om, brk), VGroup(SUM, e_1, e_2, e_3, e_4, e_5, e_6)), VGroup(eq, one).animate.scale(0.65).to_edge(RIGHT, buff=0.5))
            self.wait()
            total_length = 11
            vals1 = [0.33, 0.17, 0.12, 0.25, 0.08, 0.15]
            vals2 = [0.1, 0.2, 0.05, 0.15, 0.4, 0.1]
            vals3 = [0.18, 0.12, 0.22, 0.08, 0.20, 0.20]
            vals_uni = [1/6, 1/6, 1/6, 1/6, 1/6, 1/6]
            vals_geo = [0.34, 0.23, 0.13, 0.07, 0.06, 0.04, 0.02, 0.01]
            vals_bin = [0.01, 0.05, 0.14, 0.2, 0.25, 0.14, 0.08, 0.03]
            self.remove(align_sum)
            self.wait()
            self.play(FadeOut(SUM, eq, one))
            p_sticks = VGroup(RoundedRectangle(0.03, width=0.06, height=e_1.height).set_color(RYELL_G).set_stroke(RYELL_G).set_fill(RYELL_G, opacity=1).move_to(E[0]))
            for i in range(1, 6):
                p_sticks.add(RoundedRectangle(0.03, width=0.06, height=e_1.height).set_color(RYELL_G).set_stroke(RYELL_G).set_fill(RYELL_G, opacity=1).move_to(E[i]).align_to(p_sticks[0], UP))
            self.wait()
            hk = VGroup(*(Line(ORIGIN, [0, -0.5, 0]).set_color(SILV_G).set_stroke(SILV_G, 2).next_to(stick, DOWN, buff=-0.05).set_z_index(-1) for stick in p_sticks))
            balls = VGroup(*(VGroup(Circle(1.5).set_color(SILV_G).set_stroke(SILV_G).set_fill(SILV_G, opacity=1), TexGen(r'm', isMath=True, font_sz=170, col=GR_G).set_z_index(1)).scale_to_fit_width(vals1[i]*5).next_to(hk[i], DOWN, buff=-0.05) for i in range(6)))
            self.play(ReplacementTransform(E, p_sticks))
            self.wait()
            self.play(LaggedStart(AnimationGroup(*(GrowFromCenter(b) for b in balls)), AnimationGroup(*(GrowFromEdge(h, DOWN) for h in hk)), lag_ratio=0.7))
            hk[0].add_updater(lambda mob: mob.next_to(p_sticks[0], DOWN, buff=-0.05))
            hk[1].add_updater(lambda mob: mob.next_to(p_sticks[1], DOWN, buff=-0.05))
            hk[2].add_updater(lambda mob: mob.next_to(p_sticks[2], DOWN, buff=-0.05))
            hk[3].add_updater(lambda mob: mob.next_to(p_sticks[3], DOWN, buff=-0.05))
            hk[4].add_updater(lambda mob: mob.next_to(p_sticks[4], DOWN, buff=-0.05))
            hk[5].add_updater(lambda mob: mob.next_to(p_sticks[5], DOWN, buff=-0.05))
            balls[0].add_updater(lambda mob: mob.next_to(p_sticks[0], DOWN, buff=0.45))
            balls[1].add_updater(lambda mob: mob.next_to(p_sticks[1], DOWN, buff=0.45))
            balls[2].add_updater(lambda mob: mob.next_to(p_sticks[2], DOWN, buff=0.45))
            balls[3].add_updater(lambda mob: mob.next_to(p_sticks[3], DOWN, buff=0.45))
            balls[4].add_updater(lambda mob: mob.next_to(p_sticks[4], DOWN, buff=0.45))
            balls[5].add_updater(lambda mob: mob.next_to(p_sticks[5], DOWN, buff=0.45))
            VGroup(Dice_Q, Coin_Q, aln_left, aln_right, clock).scale(0.8).to_edge(DR)
            self.play(*(p_sticks[i].animate.become(RoundedRectangle(0.03, width=0.06, height=vals1[i]*total_length).set_color(RYELL_G).set_stroke(RYELL_G).set_fill(RYELL_G, opacity=1).move_to(p_sticks[i], aligned_edge=UP)) for i in range(6)), rate_func=rate_functions.ease_out_elastic, run_time=3.5)
            self.wait()
            self.play(*(p_sticks[i].animate.become(RoundedRectangle(0.03, width=0.06, height=vals2[i]*total_length).set_color(RYELL_G).set_stroke(RYELL_G).set_fill(RYELL_G, opacity=1).move_to(p_sticks[i], aligned_edge=UP)) for i in range(6)),
                      *(balls[i].animate.scale_to_fit_width(vals2[i]*5) for i in range(6)), run_time=2.5)
            self.play(*(p_sticks[i].animate.become(RoundedRectangle(0.03, width=0.06, height=vals3[i]*total_length).set_color(RYELL_G).set_stroke(RYELL_G).set_fill(RYELL_G, opacity=1).move_to(p_sticks[i], aligned_edge=UP)) for i in range(6)),
                      *(balls[i].animate.scale_to_fit_width(vals3[i]*5) for i in range(6)), run_time=2.5)
            self.play(GrowFromCenter(Dice_Q))
            self.wait()
            self.play(*(p_sticks[i].animate.become(RoundedRectangle(0.03, width=0.06, height=vals_uni[i]*total_length).set_color(RYELL_G).set_stroke(RYELL_G).set_fill(RYELL_G, opacity=1).move_to(p_sticks[i], aligned_edge=UP)) for i in range(6)),
                      *(balls[i].animate.scale_to_fit_width(vals_uni[i]*5) for i in range(6)), run_time=2.5)
            fracs = VGroup(TexGen(r'\frac{1}{6}', isMath=True, col=YEBLUE_G).next_to(p_sticks[i], LEFT) for i in range(6))
            self.wait()
            self.play(*(GrowFromEdge(f, RIGHT) for f in fracs))
            self.wait()
            d_ticks = VGroup(Line(ORIGIN, [0, -0.14, 0]).set_stroke(GR_G).move_to(ax.c2p(1/7*i), aligned_edge=UP) for i in range(1, 7))
            dice_outs = VGroup(*(Dice(i, scl=0.1, col=GR_G).next_to(d_ticks[i-1], DOWN) for i in range(1, 7)))
            self.play(FadeOut(fracs, p_sticks, hk))
            hk[0].clear_updaters()
            hk[1].clear_updaters()
            hk[2].clear_updaters()
            hk[3].clear_updaters()
            hk[4].clear_updaters()
            hk[5].clear_updaters()
            balls[0].clear_updaters()
            balls[1].clear_updaters()
            balls[2].clear_updaters()
            balls[3].clear_updaters()
            balls[4].clear_updaters()
            balls[5].clear_updaters()
            for i in range(6):
                p_sticks[i].next_to(d_ticks[i], UP, buff=0).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1)
            points = VGroup(*(Dot(p_sticks[i].get_edge_center(UP)).set_z_index(1).set_color(LSILV_G).set_stroke(LSILV_G).set_fill(LSILV_G) for i in range(6)))
            self.play(Create(ax[0]), ReplacementTransform(balls, points))
            self.play(*(Create(t) for t in d_ticks), Create(ax[1]))
            pmassf = TexGen(r'Probability Mass Function', font_sz=60, col=LSILV_G).to_edge(UP)
            pmf = TexGen(r'PMF', font_sz=60, col=LSILV_G).move_to(pmassf, aligned_edge=UP)
            pf = TexGen(r'p', font_sz=60, col=LSILV_G, isMath=True).move_to(pmf)
            neq = TexGen(r'\neq', font_sz=60, col=GR_G, isMath=True).next_to(pf, RIGHT).shift(0.15*UP)
            Pf = TexGen(r'P', font_sz=60, col=YEBLUE_G, isMath=True).next_to(neq, RIGHT)
            omega = TexGen(r'\Omega', isMath=True, font_sz=60, col=GR_G).next_to(ax[0], DR).shift(0.5*LEFT)
            ax_P = Axes(x_range=[0, 1], x_length=4, y_range=[0, 1], y_length=2, tips=True, axis_config={"tip_shape": StealthTip, "tip_height": 0.2}).set_stroke(GR_G, width=4).set_fill(GR_G).next_to(Pf, RIGHT, aligned_edge=UP).shift(0.1*DOWN)
            P_ticks = VGroup(deepcopy(d_ticks[0]).scale_to_fit_height(0.09).move_to(ax_P.c2p(0.05), aligned_edge=UP),
                             deepcopy(d_ticks[0]).scale_to_fit_height(0.09).move_to(ax_P.c2p(0.2), aligned_edge=UP),
                             deepcopy(d_ticks[0]).scale_to_fit_height(0.09).move_to(ax_P.c2p(0.6), aligned_edge=UP))
            e1 = SetGen([Dice(1)], col=YELL_G).scale(0.25).next_to(P_ticks[1], DOWN, buff=0.17)
            e14 = SetGen([Dice(1), Dice(4)], col=YELL_G).scale(0.25).next_to(P_ticks[2], DOWN, buff=0.17)
            dots1 = TexGen(r'\dots', isMath=True, font_sz=30, col=YELL_G).next_to(e1, RIGHT, buff=0.25)
            dots2 = deepcopy(dots1).next_to(e14, RIGHT, buff=0.25)
            empty_set = TexGen(r'\{\}', isMath=True, font_sz=50, col=YELL_G).scale_to_fit_height(e1.height).next_to(P_ticks[0], DOWN, buff=0.17)
            power_set = TexGen(r'\mathcal{P}(\Omega)', isMath=True, font_sz=50, col=YELL_G).scale_to_fit_height(e1.height*0.9).next_to(ax_P.c2p(1.04), DOWN, buff=0.25)
            P_stick1 = RoundedRectangle(0.01, width=0.02, height=1).set_color(RYELL_G).set_stroke(RYELL_G).set_fill(RYELL_G, opacity=1).next_to(P_ticks[1], UP, buff=0)
            P_stick14 = VGroup(deepcopy(P_stick1).next_to(P_ticks[2], UP, buff=0), deepcopy(P_stick1).next_to(P_ticks[2], UP, buff=0).shift(UP))
            P_dots = VGroup(Dot(P_ticks[0].get_edge_center(UP)).set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G), 
                            Dot(P_stick1.get_edge_center(UP)).set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G),
                            Dot(P_stick14.get_edge_center(UP)).set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G)).set_z_index(1)
            kg_tick = Line(ORIGIN, [0.14, 0, 0]).set_stroke(RGR_G).move_to(ax.c2p([0, 1]), aligned_edge=RIGHT).set_y(points.get_y())
            m_tick = Line(ORIGIN, [0.09, 0, 0]).set_stroke(RGR_G).move_to(ax_P.c2p([0, 0.5]), aligned_edge=RIGHT)
            kg2 = TexGen(r'2 kg', font_sz=60, col=LSILV_G).next_to(kg_tick, LEFT)
            kg16 = TexGen(r'$\frac{1}{6}$', font_sz=60, col=LSILV_G).next_to(kg_tick, LEFT)
            meters = TexGen(r'$\frac{1}{6}$ m', font_sz=40, col=YEBLUE_G).next_to(m_tick, LEFT)
            dsh_hline = DashedLine(points[0], kg_tick.get_edge_center(RIGHT)).set_stroke(GR_G, 3).set_z_index(-1)
            dsh_hline_P = DashedLine(P_dots[1], m_tick.get_edge_center(RIGHT)).set_stroke(GR_G, 3).set_z_index(-1)
            dsh_vline = DashedLine(d_ticks[0].get_edge_center(UP), points[0]).set_stroke(GR_G, 3).set_z_index(-1)
            self.wait()
            self.play(Draw(pmassf))
            self.wait()
            self.play(ReplacementTransform(pmassf, pmf))
            self.wait()
            self.play(ReplacementTransform(pmf, pf))
            self.wait()
            self.play(Draw(neq), Draw(Pf))
            self.wait()
            self.play(pf.animate.next_to(ax[1], UL).shift(0.5*DOWN), FadeOut(neq))
            self.play(Draw(omega))
            self.wait()
            self.play(*(GrowFromPoint(dice_outs[i], d_ticks[i].get_edge_center(DOWN)) for i in range(6)))
            self.wait()
            self.play(LaggedStart(Create(dsh_vline), Create(dsh_hline), GrowFromEdge(VGroup(kg2, kg_tick), RIGHT), lag_ratio=0.9))
            self.wait()
            self.play(GrowFromPoint(ax_P, ax_P.get_corner(DL)))
            self.play(Draw(power_set))
            self.wait()
            self.play(GrowFromPoint(dots1, dots1.get_edge_center(UP)+[0, 0.4, 0]), GrowFromPoint(dots2, dots2.get_edge_center(UP)+[0, 0.4, 0]), GrowFromPoint(empty_set, P_ticks[0].get_edge_center(DOWN)), GrowFromPoint(e1, P_ticks[1].get_edge_center(DOWN)), GrowFromPoint(e14, P_ticks[2].get_edge_center(DOWN)), *(GrowFromEdge(t, UP) for t in P_ticks))
            self.play(*(GrowFromPoint(P_dots[i], P_ticks[i].get_edge_center(UP)) for i in range(3)))
            self.wait()
            self.play(GrowFromPoint(P_stick1, P_ticks[1].get_edge_center(UP)), GrowFromPoint(P_stick14, P_ticks[2].get_edge_center(UP)))
            self.wait()
            self.play(LaggedStart(Create(dsh_hline_P), GrowFromEdge(VGroup(meters, m_tick), RIGHT), lag_ratio=0.9))
            self.wait()
            self.play(FadeOut(Pf, ax_P, power_set, empty_set, e1, e14, P_dots, P_stick1, P_stick14, P_ticks, meters, m_tick, dsh_hline_P, dots1, dots2))
            self.play(ReplacementTransform(kg2, kg16))
            self.play(FadeOut(dsh_hline, dsh_vline))
            self.wait()
            self.play(*(GrowFromEdge(stick, DOWN) for stick in p_sticks))
            self.wait()
            p_sticks[0].save_state()
            p_sticks[3].save_state()
            self.play(p_sticks[0].animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1))
            self.wait()
            self.play(p_sticks[3].animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1))
            self.wait()
            self.play(Restore(p_sticks[3]), Restore(p_sticks[0]))
            self.wait()
            o_height = dice_outs[0].height
            coin_outs = Group(deepcopy(HCoin_GR).scale_to_fit_height(o_height).move_to(dice_outs[1]), deepcopy(TCoin_GR).scale_to_fit_height(dice_outs[0].height).move_to(dice_outs[4]))
            p_sticks_coins = VGroup(RoundedRectangle(0.03, width=0.06, height=total_length*0.5).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1).next_to(d_ticks[1], UP, buff=0),
                                    RoundedRectangle(0.03, width=0.06, height=total_length*0.5).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1).next_to(d_ticks[4], UP, buff=0))
            self.play(*(dice_outs[i].animate.scale(0).move_to(d_ticks[i].get_edge_center(DOWN)) for i in range(6)),
                      *(stick.animate.scale(0).move_to(stick, aligned_edge=DOWN) for stick in p_sticks),
                      *(points[i].animate.scale(0).move_to(d_ticks[i], aligned_edge=UP) for i in range(6)),
                      ReplacementTransform(Dice_Q, Coin_Q), FadeOut(kg16, kg_tick))
            self.play(d_ticks[0].animate.move_to(d_ticks[1]), d_ticks[2].animate.move_to(d_ticks[1]), GrowFromPoint(coin_outs[1], d_ticks[4].get_edge_center(DOWN)),
                      d_ticks[3].animate.move_to(d_ticks[4]), d_ticks[5].animate.move_to(d_ticks[4]), GrowFromPoint(coin_outs[0], d_ticks[1].get_edge_center(DOWN)))
            coin_points = VGroup(*(Dot(p_sticks_coins[i].get_edge_center(UP)).set_z_index(1).set_color(LSILV_G).set_stroke(LSILV_G).set_fill(LSILV_G) for i in range(2)))
            self.play(*(GrowFromEdge(VGroup(coin_points[i], p_sticks_coins[i]), DOWN) for i in range(2)))
            self.wait()
            self.play(coin_outs[0].animate.scale(0).move_to(d_ticks[1].get_edge_center(DOWN)), coin_outs[1].animate.scale(0).move_to(d_ticks[4].get_edge_center(DOWN)),
                      *(stick.animate.scale(0).move_to(stick, aligned_edge=DOWN) for stick in p_sticks_coins),
                      coin_points[0].animate.scale(0).move_to(d_ticks[1], aligned_edge=UP), coin_points[1].animate.scale(0).move_to(d_ticks[4], aligned_edge=UP),
                      GrowFromEdge(aln_right, DL), GrowFromEdge(aln_left, DR))
            a_ticks = VGroup(Line(ORIGIN, [0, -0.14, 0]).set_stroke(GR_G).move_to(ax.c2p(1/10.5*i), aligned_edge=UP) for i in range(1, 9))
            one_stick = RoundedRectangle(0.03, width=0.06, height=total_length*1).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1).next_to(a_ticks[0], UP, buff=0)
            points[0].move_to(one_stick.get_edge_center(UP))
            a_outs = VGroup(*(TexGen(rf'{i}', isMath=True, col=GR_G).scale_to_fit_height(o_height*0.8).next_to(a_ticks[i-1], DOWN) for i in range(1, 9)))
            a_outs.add(TexGen(r'\ldots', isMath=True, col=GR_G, font_sz=50).next_to(a_outs[-1], RIGHT, buff=0.4))
            p_sticks_a = VGroup(*(RoundedRectangle(0.03, width=0.06, height=total_length*vals_geo[i]).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1).next_to(a_ticks[i], UP, buff=0) for i in range(8)))
            p_sticks_a2 = VGroup(*(RoundedRectangle(0.03, width=0.06, height=total_length*vals_bin[i]).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1).next_to(a_ticks[i], UP, buff=0) for i in range(8)))
            points_a = VGroup(*(Dot(p_sticks_a[i].get_edge_center(UP)).set_z_index(1).set_color(LSILV_G).set_stroke(LSILV_G).set_fill(LSILV_G) for i in range(8)))
            points_a2 = VGroup(*(Dot(p_sticks_a2[i].get_edge_center(UP)).set_z_index(1).set_color(LSILV_G).set_stroke(LSILV_G).set_fill(LSILV_G) for i in range(8)))
            self.play(LaggedStart(ReplacementTransform(d_ticks, a_ticks), AnimationGroup(*(GrowFromPoint(a_outs[i], a_ticks[i].get_edge_center(DOWN)) for i in range(8))), Draw(a_outs[-1]), lag_ratio=0.9))
            self.wait()
            self.play(GrowFromEdge(VGroup(one_stick, points[0]), DOWN))
            self.wait()
            self.play(ReplacementTransform(one_stick, p_sticks_a[0]), ReplacementTransform(points[0], points_a[0]),
                      *(GrowFromEdge(VGroup(points_a[i], p_sticks_a[i]), DOWN) for i in range(1, 8)))
            self.wait()
            self.play(*(p_sticks_a[i].animate.become(p_sticks_a2[i]) for i in range(8)), *(points_a[i].animate.become(points_a2[i]) for i in range(8)))
            self.wait()
            inf_sum = TexGen(r'\sum_{n=1}^{\infty}', col=YEBLUE_G, isMath=True).shift(3*RIGHT)
            one = TexGen(r'1', col=YEBLUE_G, isMath=True, font_sz=70).move_to(inf_sum)
            self.play(p_sticks_a.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1))
            self.wait()
            self.play(Draw(inf_sum))
            self.wait()
            self.play(ReplacementTransform(inf_sum, one))
            self.wait()
            self.play(p_sticks_a.animate.set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1), FadeOut(one))
            self.play(Coin_Q[1].animate.scale(0.5).shift(0.24*DOWN), GrowFromPoint(clock, Coin_Q.get_center()),  aln_left.animate.scale(0).move_to(aln_left, aligned_edge=DR), aln_right.animate.scale(0).move_to(aln_right, aligned_edge=DL),
                      *(p_sticks_a[i].animate.scale(0).move_to(p_sticks_a[i], aligned_edge=DOWN) for i in range(8)), *(points_a[i].animate.scale(0).move_to(a_ticks[i]) for i in range(8)),
                      a_ticks.animate.stretch_to_fit_height(0), *(a_outs[i].animate.scale(0).move_to(a_ticks[i].get_edge_center(DOWN)) for i in range(8)), a_outs[-1].animate.scale(0).set_y(a_ticks.get_y()))
            self.remove(a_ticks)
            self.wait()
            self.play(FadeOut(ax, pf, omega))
            self.wait()
            
        def play_density():
            VGroup(Coin_Q, clock, deepcopy(aln_left), deepcopy(aln_right)).scale(0.8).to_edge(DR)
            VGroup(Dice_Q, aln_left, aln_right).scale(0.8).to_edge(UR)
            Coin_Q[1].scale(0.5).shift(0.24*DOWN)
            self.add(Coin_Q, clock)
            sigma = 0.12
            mu = 0.5
            bell_curve = ax.plot(lambda x: 0.9*(np.exp(-((x-mu)**2)/(2*sigma**2))), x_range=[0, 0.97, 0.0001], color=LSILV_G, stroke_width=6)
            A_1 = ax.get_area(bell_curve, [0, 1], color=RGR_G, opacity=1).set_z_index(-1)
            A_2 = ax.get_area(bell_curve, [0.3, 0.5], color=YEBLUE_G, opacity=1).set_z_index(-1)
            A_3 = ax.get_area(bell_curve, [0.3, 0.302], color=YEBLUE_G, opacity=1).set_z_index(-1)
            A_4 = ax.get_area(bell_curve, [0, 1], color=YEBLUE_G, opacity=1).set_z_index(-1)
            self.play(GrowFromCenter(Dice_Q))
            sticks = VGroup(RoundedRectangle(0.03, width=0.06, height=1.7).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1))
            for i in range(5):
                sticks.add(RoundedRectangle(0.03, width=0.06, height=1.7).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1).next_to(sticks[i], RIGHT, buff=8.7/6))
            sticks.next_to(Dice_Q, DOWN, buff=0.12).stretch_to_fit_width(A_1.width).set_x(A_1.get_x())
            omega_dice = TexGen(r'\Omega', font_sz=100, col=GR_G, isMath=True).next_to(sticks, LEFT, buff=1.5)
            self.wait()
            self.play(LaggedStart(*(GrowFromEdge(s, LEFT) for s in sticks)))
            self.wait()
            self.play(Draw(omega_dice))
            self.wait()
            sticks.save_state()
            self.play(sticks[2].animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1))
            self.wait()
            self.play(sticks[3].animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1))
            self.wait()
            self.play(*(sticks[i].animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1) for i in [0, 1, 4, 5]))
            self.wait()
            self.play(Restore(sticks))
            self.wait()
            sticks_time = VGroup(RoundedRectangle(0.01, width=0.06, height=1.7).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1))
            for i in range(100):
                sticks_time.add(RoundedRectangle(0.01, width=0.06, height=1.7).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1).next_to(sticks_time[i], RIGHT, buff=-0.03))
            sticks_time.next_to(Coin_Q, UP, buff=0.12).stretch_to_fit_width(A_1.width).set_x(A_1.get_x())
            rect = Rectangle(height=1.7, width=sticks_time.width).set_color(RGR_G).set_stroke(RGR_G).set_fill(RGR_G, opacity=1).move_to(sticks_time)
            omega_time = TexGen(r'\Omega', font_sz=100, col=GR_G, isMath=True).next_to(sticks_time, LEFT, buff=1.5)
            zero = TexGen(r'0', font_sz=60, col=GR_G, isMath=True).next_to(sticks_time[0], DOWN)
            six = TexGen(r'6', font_sz=60, col=GR_G, isMath=True).next_to(sticks_time[-1], DOWN)
            inf = TexGen(r'\infty', font_sz=60, col=GR_G, isMath=True).move_to(six)
            self.play(FadeIn(omega_time, target_position=omega_dice))
            self.wait()
            self.play(Draw(zero))
            self.wait()
            self.play(Draw(six))
            self.wait()
            self.play(LaggedStart(*(GrowFromEdge(s, LEFT) for s in sticks_time)))
            self.wait()
            self.play(ReplacementTransform(sticks_time, rect))
            self.wait()
            e_2 = RoundedRectangle(0.02, width=0.03, height=1.7).set_color(YELL_G).set_stroke(YELL_G).set_fill(YELL_G, opacity=1).move_to(rect).shift(0.25*rect.width*LEFT)
            e_2_cp = deepcopy(e_2)
            e_2_cp2 = deepcopy(e_2)
            e_23 = Rectangle(width=0.25*rect.width, height=1.7).set_color(YELL_G).set_stroke(YELL_G).set_fill(YELL_G, opacity=1).move_to(rect).align_to(e_2, LEFT)
            e_23_cp = Rectangle(width=0.25*rect.width, height=1.7).set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1).move_to(rect).align_to(e_2, LEFT)
            two = TexGen(r'2', font_sz=60, col=GR_G, isMath=True).next_to(e_2, DOWN).set_y(six.get_y())
            three = TexGen(r'3', font_sz=60, col=GR_G, isMath=True).move_to(rect).set_y(six.get_y())
            in_B = TexGen(r'\in \mathcal{B}(\Omega)', font_sz=60, col=YELL_G, isMath=True).next_to(e_23, UP)
            self.play(Draw(two))
            self.play(FadeIn(e_2))
            self.wait()
            self.play(Draw(three))
            self.play(ReplacementTransform(e_2, e_23))
            rect.save_state()
            self.wait()
            self.play(GrowFromEdge(in_B, DOWN))
            self.wait()
            self.play(FadeOut(three), ReplacementTransform(e_23, e_2_cp), in_B.animate.set_x(two.get_x()))
            self.wait()
            self.play(FadeOut(in_B))
            self.wait()
            self.play(e_2_cp.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1))
            self.wait()
            self.play(ReplacementTransform(e_2_cp, e_23_cp), Draw(three))
            self.wait()
            self.play(e_23_cp.animate.set_color(RED_G).set_stroke(RED_G).set_fill(RED_G, opacity=1).set_z_index(1))
            self.wait()
            rect.save_state()
            e_23_cp.save_state()
            self.play(VGroup(rect, e_23_cp).animate.stretch_to_fit_height(0.3).move_to(rect, aligned_edge=DOWN))
            self.wait()
            self.play(Restore(rect), Restore(e_23_cp))
            self.wait()
            self.play(e_23_cp.animate.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1))
            self.wait()
            self.play(ReplacementTransform(e_23_cp, e_2_cp2.set_color(YEBLUE_G).set_stroke(YEBLUE_G).set_fill(YEBLUE_G, opacity=1)), FadeOut(three))
            self.wait()
            self.play(FadeOut(e_2_cp2, two, Dice_Q, sticks, omega_dice, omega_time))
            self.wait()
            zero_line = Line(ax.c2p(0), ax.c2p(0.97)).set_color(GR_G).set_stroke(GR_G, 5)
            self.play(rect.animate.stretch_to_fit_height(zero_line.height).move_to(rect, aligned_edge=DOWN))
            self.wait()
            inject = ImageMobject("inject.png").scale_to_fit_height(1.5).next_to(A_1, DOWN, buff=-0.13)
            pause = VGroup(RoundedRectangle(0.09, width=0.7, height=1.4).set_color(LSILV_G).set_stroke(LSILV_G).set_fill(LSILV_G, opacity=1),
                           RoundedRectangle(0.09, width=0.7, height=1.4).set_color(LSILV_G).set_stroke(LSILV_G).set_fill(LSILV_G, opacity=1).shift(RIGHT)).to_edge(UL)
            self.play(LaggedStart(FadeIn(inject, target_position=inject.get_edge_center(DOWN)), GrowFromEdge(A_1, DOWN, run_time=10, rate_func=rate_functions.ease_out_quad), lag_ratio=0.68))
            self.add(pause)
            self.wait()
            dns_rect = RoundedRectangle(0.02, width=0.3, height=0.3).set_color(LSILV_G).set_stroke(LSILV_G).set_fill(opacity=0).next_to(inject, UP, buff=-0.1)
            self.play(Create(dns_rect))
            self.wait()
            self.play(dns_rect.animate.shift(1.7*LEFT))
            self.wait()
            self.play(Create(bell_curve))
            self.play(FadeOut(rect, A_1, pause, dns_rect, inject), Create(ax))
            self.wait()
            pdenf = TexGen(r'Probability Density Function', font_sz=60, col=LSILV_G).to_edge(UP)
            pdf = TexGen(r'PDF', font_sz=60, col=LSILV_G).move_to(pdenf, aligned_edge=UP)
            pf = TexGen(r'p', font_sz=60, col=LSILV_G, isMath=True).move_to(pdf)
            self.play(Draw(pdenf))
            self.wait()
            self.play(ReplacementTransform(pdenf, pdf))
            self.wait()
            self.play(ReplacementTransform(pdf, pf))
            self.wait()
            self.play(pf.animate.next_to(ax[1], UL).shift(0.5*DOWN))
            self.wait()
            a = TexGen(r'a', font_sz=60, col=GR_G, isMath=True).move_to([A_2.get_edge_center(LEFT)[0], six.get_y(), 0]).align_to(zero, DOWN)
            b = TexGen(r'b', font_sz=60, col=GR_G, isMath=True).move_to([A_2.get_edge_center(RIGHT)[0], six.get_y(), 0]).align_to(zero, DOWN)
            integral = TexGen(r'\int_{a}^{b}', isMath=True, font_sz=60, col=RYEBLUE_G).next_to(A_2, UP, buff=-1.5).shift(1.5*LEFT)
            integral2 = TexGen(r'\int_{a}^{a}', isMath=True, font_sz=60, col=RYEBLUE_G).move_to(integral, aligned_edge=DOWN)
            integral3 = TexGen(r'\int_{0}^{\infty}', isMath=True, font_sz=60, col=RYEBLUE_G).move_to(integral, aligned_edge=DOWN)
            one = TexGen(r'1', isMath=True, font_sz=100, col=RYEBLUE_G).move_to(integral)
            self.play(LaggedStart(Draw([a, b]), FadeIn(A_2), lag_ratio=0.5))
            self.play(Draw(integral))
            self.wait()
            self.play(ReplacementTransform(A_2, A_3), ReplacementTransform(integral, integral2), FadeOut(b))
            self.wait()
            self.play(ReplacementTransform(six, inf))
            self.wait()
            self.play(ReplacementTransform(A_3, A_4), ReplacementTransform(integral2, integral3))
            self.wait()
            self.play(ReplacementTransform(integral3, one))
            self.wait()
            self.play(FadeOut(Coin_Q, ax, clock, a, zero, inf, one, pf, bell_curve, A_4))
            self.wait()

        def play_model():
            events = TexGen(r'Events', font_sz=100, col=YELL_G).to_edge(DOWN, buff=1)
            event_line = deepcopy(out_line).move_to([0, -2, 0], aligned_edge=DOWN)
            discrete = TexGen(r'discrete', font_sz=50, col=GR_G).move_to([-4.7, outs.get_y(), 0])
            cont = TexGen(r'continuous', font_sz=50, col=GR_G).move_to([4.7, outs.get_y(), 0])
            p_d = TexGen(r'p:\Omega \to [0, 1]', font_sz=50, col=GR_G, isMath=True).next_to(discrete, DOWN)
            p_c = TexGen(r'p:\Omega \to [0, \infty[', font_sz=50, col=GR_G, isMath=True).next_to(cont, DOWN)
            P_d = TexGen(r'P:\mathcal{P}(\Omega) \to [0, 1]', font_sz=50, col=GR_G, isMath=True).next_to(events, LEFT).set_x(discrete.get_x())
            P_c = TexGen(r'P:\mathcal{B}(\Omega) \to [0, 1]', font_sz=50, col=GR_G, isMath=True).next_to(events, RIGHT).set_x(cont.get_x())
            self.play(Draw(exp))
            self.wait()
            self.play(GrowFromPoint(VGroup(out_line, outs), point=rot_point, point_color=BLACK))
            self.wait()
            self.play(GrowFromEdge(discrete, RIGHT))
            self.wait()
            self.play(GrowFromPoint(p_d, discrete.get_edge_center(DOWN)))
            self.wait()
            self.play(GrowFromEdge(cont, LEFT))
            self.wait()
            self.play(GrowFromPoint(p_c, cont.get_edge_center(DOWN)))
            self.wait()
            self.play(GrowFromPoint(VGroup(event_line, events), point=event_line.get_edge_center(UP), point_color=BLACK))
            self.wait()
            self.play(GrowFromPoint(P_d, p_d.get_edge_center(DOWN)))
            self.wait()
            self.play(GrowFromPoint(P_c, p_c.get_edge_center(DOWN)))
            self.wait()



        # GLOBALS
        prob = TexGen(r'Probability', col=YEBLUE_G, font_sz=100).to_edge(UP)
        rnd = wordGen("Randomness").to_edge(UP).set_x(0)
        Qm = TexGen(r'?', font_sz=100, col=YELL_G)
        pc = TexGen(r'\%', font_sz=300, col=RED_G)
        pc_up_circ = SVGMobject("pc_circ.svg").scale(0.65).set_stroke(width=1).set_color(WHITE_G).move_to(pc, aligned_edge=UL)
        pc_down_circ = SVGMobject("pc_circ.svg").scale(0.65).set_stroke(width=1).set_color(WHITE_G).move_to(pc, aligned_edge=DR)
        pc_line = SVGMobject("pc_line.svg").scale(1.27).set_stroke(width=1).set_color(WHITE_G)
        pc = VGroup(pc_up_circ, pc_down_circ, pc_line).scale(0.35).set_stroke(GR_G).set_color(GR_G).set_fill(GR_G, opacity=1)
        exp = TexGen(r'Experiment', font_sz=100, col=YELL_G).move_to(rnd, aligned_edge=UP) 
        outs = TexGen(r'Outcomes', font_sz=100, col=YELL_G).shift(0.2*UP)
        R = RoundedRectangle(1, width=5.5, height=5.5).set_color(YELL_G).set_stroke(YELL_G).set_fill(YELL_G, opacity=1)
        C = Circle(0.5).set_color(BLACK_G).set_stroke(BLACK_G).set_fill(BLACK_G, opacity=1)
        Dice_Q = VGroup(deepcopy(R), TexGen(r'?', font_sz=500, col=BLACK_G, stroke_w=3)).scale(0.2).move_to(exp, aligned_edge=UP)
        Coin = Cylinder(Dice_Q.height/2, 0.2).set_color(YELL_G).set_stroke(YELL_G).set_fill(YELL_G, opacity=1).shift(0.1*IN)
        FlatCoin = Circle(Coin.radius).set_color(YELL_G).set_stroke(YELL_G).set_fill(YELL_G, opacity=1).move_to(exp, aligned_edge=UP)
        HCoin = Group(deepcopy(FlatCoin).move_to([-2, 0, 0]), ImageMobject("maku.png").scale_to_fit_height(FlatCoin.height-0.1).move_to([-2, 0, 0]))
        TCoin = Group(deepcopy(FlatCoin).move_to([2, 0, 0]), ImageMobject("tail.png").scale_to_fit_height(FlatCoin.height-0.1).move_to([2, 0, 0]))
        HCoin_GR = Group(deepcopy(FlatCoin).set_color(GR_G).set_stroke(GR_G).set_fill(GR_G, opacity=1).move_to([-2, 0, 0]), ImageMobject("maku_gr.png").scale_to_fit_height(FlatCoin.height-0.1).move_to([-2, 0, 0]))
        TCoin_GR = Group(deepcopy(FlatCoin).set_color(GR_G).set_stroke(GR_G).set_fill(GR_G, opacity=1).move_to([2, 0, 0]), ImageMobject("tail_gr.png").scale_to_fit_height(FlatCoin.height-0.1).move_to([2, 0, 0]))
        ECoin = Group(Coin, ImageMobject("maku.png").scale_to_fit_height(FlatCoin.height-0.1).shift(0.03*IN))
        Coin_Q = VGroup(deepcopy(FlatCoin), deepcopy(Dice_Q[1]).set_z_index(1)).move_to(exp, aligned_edge=UP)
        H_line = BranchLine(-2)
        T_line = BranchLine(2)
        fade_rect = Rectangle(BLACK, height=20, width=20).set_z_index(-0.5).set_fill(BLACK, opacity=1)
        aln_right = SVGMobject("aln.svg").set_color(GREEN_G).set_stroke(GREEN_G).set_fill(GREEN_G).scale(0.15).move_to([0.6, 3.5, 0]).set_z_index(-0.1)
        aln_left = deepcopy(aln_right).flip().move_to([-0.6, 3.5, 0])    
        clock = VGroup(RoundedRectangle(0.02, width=0.04, height=Coin.radius-0.24).set_color(BR_G).set_fill(BR_G, opacity=1).set_stroke(BR_G).move_to(Coin_Q.get_center(), aligned_edge=DOWN).set_z_index(1).rotate(-PI/2.7, about_point=Coin_Q.get_center()),
                       RoundedRectangle(0.02, width=0.04, height=Coin.radius-0.09).set_color(BR_G).set_fill(BR_G, opacity=1).set_stroke(BR_G).move_to(Coin_Q.get_center(), aligned_edge=DOWN).set_z_index(1))
        Omega_D = SetGen([Dice(i) for i in range(1, 7)], col=YELL_G).move_to(ORIGIN)
        Ds = Omega_D[1:][::2]
        dice_lines = VGroup()
        for d in Ds:
            dice_lines.add(BranchLine(d.get_x()))
        Omega = TexGen(r'\Omega=', isMath=True, col=YELL_G, font_sz=100)
        Omega_D_scl = deepcopy(Omega_D).scale_to_fit_height(1.4*Omega.height).next_to(Omega, RIGHT, buff=0.4).shift(0.05*DOWN)
        O = VGroup(Omega, Omega_D_scl).to_edge(UP).set_x(0)
        pshift = 2.2
        p_set = TexGen(r'P(\phantom{\textup{Set}})', isMath=True, font_sz=100, col=YEBLUE_G).shift(pshift*DOWN)
        e_set = TexGen(r'Set', font_sz=100, col=YELL_G).move_to(p_set).shift(0.42*RIGHT+0.1*UP)
        measure = TexGen(r'Measure', font_sz=100, col=YEBLUE_G)
        theory = TexGen(r'Theory', font_sz=100, col=YEBLUE_G).next_to(measure, RIGHT, aligned_edge=UP, buff=0.4)
        VGroup(measure, theory).set_x(0)
        m = TexGen(r'\mu', font_sz=115, col=YEBLUE_G, isMath=True).to_edge(UP).to_edge(LEFT, buff=0.8)
        r1 = TexGen(r'\ding{182}', col=GR_G, font_sz=60).next_to(m, RIGHT, aligned_edge=UP).shift(3*RIGHT)
        r2 = TexGen(r'\ding{183}', col=GR_G, font_sz=60).next_to(r1, RIGHT).shift(3*RIGHT)
        r3 = TexGen(r'\ding{184}', col=GR_G, font_sz=60).next_to(r2, RIGHT).shift(3*RIGHT)
        p = TexGen(r'P', isMath=True, font_sz=100, col=YEBLUE_G).move_to(m, aligned_edge=UP)
        ax = Axes(x_range=[0, 1], x_length=8, y_range=[0, 1], y_length=5, tips=True, axis_config={"tip_shape": StealthTip, "tip_height": 0.3}).set_stroke(GR_G, width=5).set_fill(GR_G)
        

        # ANIMATE
        play_intro()
        play_random()
        play_exp()
        play_outs()
        play_events()
        play_set()
        play_measure()
        play_rules()
        play_prob()
        play_mass()
        play_density()
        play_model()
