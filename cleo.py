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
        YT_G = color_gradient([ManimColor.from_hex("#FF0033"), ManimColor.from_hex("#FF0033")], 200)
        
        BGRAY_G = color_gradient([ManimColor.from_hex("#7E7E7E"), ManimColor.from_hex("#B1B1B1")], 200)
        BGRAY_G = color_gradient([ManimColor.from_hex("#5F5F5F"), ManimColor.from_hex("#949494")], 200)
        GRAY_G = color_gradient([ManimColor.from_hex("#212121"), ManimColor.from_hex("#505050")], 200)
        GRAY_G = color_gradient([ManimColor.from_hex("#949494"), ManimColor.from_hex("#949494")], 200)
        MAG_G = color_gradient([ManimColor.from_hex("#BA00B7"), ManimColor.from_hex("#BA00B7")], 200)
        USR_G = color_gradient([ManimColor.from_hex("#0077FF"), ManimColor.from_hex("#0077FF")], 200)
        BROWSER_G = color_gradient([ManimColor.from_hex("#212121"), ManimColor.from_hex("#212121")], 200)
        BAR_G = color_gradient([ManimColor.from_hex("#343434"), ManimColor.from_hex("#343434")], 200)
        LINK_G = color_gradient([ManimColor.from_hex("#0091FF"), ManimColor.from_hex("#0091FF")], 200)
        PORTRAIT_G = color_gradient([ManimColor.from_hex("#949494"), ManimColor.from_hex("#111111")], 200)

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
                
        def DrawTxt(txt, stroke_w=2.0) -> Animation:
            draw_anims = []
            for t in txt:
                draw_anims.append(DrawBorderThenFill(t, stroke_color=t.get_stroke_colors(), stroke_width=stroke_w, run_time=1))
            return draw_anims
        
        def BounceIn(mobjects, run_t=0.5) -> Animation:
            bounce_anims = []
            for mob in mobjects:
                bounce_anims.append(GrowFromCenter(mob, rate_func=rate_functions.ease_out_back, run_time=run_t))
            return bounce_anims
        
        def RectAroundImage(img, col1, col2, additionals=9):
            rects = VGroup(SurroundingRectangle(img, corner_radius=0.2, color=col1, buff=0))
            for i in range(2):
                rects.add(SurroundingRectangle(rects[i], corner_radius=0.2, color=col1, buff=0.01))
            for i in range(additionals-3):
                rects.add(SurroundingRectangle(rects[i+2], corner_radius=0.2, color=col2, buff=0.01))
            return rects
        
        def PersonGen(txt):
            return VGroup(SVGMobject("person.svg", height=1, stroke_width=0), Circle(0.08, BLACK).set_stroke(color=BLACK).set_fill(color=BLACK, opacity=1).shift(0.24*UP+0.12*LEFT),
                          Circle(0.08, BLACK).set_stroke(color=BLACK).set_fill(color=BLACK, opacity=1).shift(0.24*UP+0.12*RIGHT), TexGen(rf'{txt}', col=WHITE_G, font_sz=31, stroke_w=1.8).shift(0.29*DOWN))
           
        def PostGen(txt_Group, img, name, date, answer=True, w_buff=1, h_buff=0.4):
            txt_Group.set_z_index(0.5)
            if txt_Group.height+0.4 < 1:
                txt_container_height = 0.9
            else:
                txt_container_height = txt_Group.height+h_buff
            txt_container = RoundedRectangle(corner_radius=0.2, width=txt_Group.width+w_buff, height=txt_container_height).set_fill(WHITE_G, opacity=1).set_stroke(width=0).set_z_index(0.5)
            txt_Group.move_to(txt_container)
            img.scale_to_fit_width(0.8).set_z_index(1)
            img_rects = RectAroundImage(img=img, col1=USR_G, col2=USR_G, additionals=6).set_z_index(1)
            name.next_to(img_rects, buff=0.08)
            user_container = RoundedRectangle(corner_radius=0.2, width=Group(img_rects, name).width+0.25, height=Group(img_rects, name).height+0.06).set_fill(USR_G, opacity=1).set_stroke(width=0).move_to(Group(img_rects, name)).shift(0.09*RIGHT) 
            if answer:
                Group(user_container, img, img_rects, name).next_to(txt_container, RIGHT, aligned_edge=UP, buff=-0.2).shift(0.2*UP).set_z_index(1)
                date.next_to(user_container, 0.5*DOWN, aligned_edge=RIGHT).shift(0.1*LEFT)
            else:
                Group(user_container, img, img_rects, name).next_to(txt_container, LEFT, aligned_edge=UP, buff=-0.2).shift(0.2*UP).set_z_index(1)
                date.next_to(user_container, 0.5*DOWN, aligned_edge=LEFT).shift(0.1*RIGHT)
            return Group(txt_container, txt_Group, user_container, img, img_rects, name, date).move_to(ORIGIN)

        def Post(mob, answer=True):
            if answer:
                return LaggedStart(GrowFromCenter(mob[2:6], rate_func=rush_from, run_time=0.3), Create(mob[-1]), GrowFromPoint(Group(*mob[0:2]), mob[2].get_center()-[1, 0, 0]))
            else:
                return LaggedStart(GrowFromCenter(mob[2:6], rate_func=rush_from, run_time=0.3), Create(mob[-1]), GrowFromPoint(Group(*mob[0:2]), mob[2].get_center()+[1, 0, 0]))
            
        def play_intro():
            nov11 = TexGen(r'Nov 11, 2013', font_sz=20, col=GRAY_G).next_to(bar, DOWN)
            need_help = TexGen(r'I need help with this integral:', col=BLACK_G, font_sz=25)
            cleo_I = TexGen(r'I = \int_{-1}^{1} \frac{1}{x}\sqrt{\frac{1+x}{1-x}}\ln\!\left(\frac{2x^{2}+2x+1}{2x^{2}-2x+1}\right)\,dx', isMath=True, font_sz=25, col=BLACK_G).next_to(need_help, DOWN)
            cleo_sol_laila = TexGen(r'I = 4 \pi \textup{arccot}\sqrt{\phantom{\phi}}', isMath=True, font_sz=25, col=BLACK_G)
            phi = TexGen(r'\phi', isMath=True, font_sz=25, col=LINK_G).move_to(cleo_sol_laila, aligned_edge=RIGHT).set_z_index(1).shift(0.02*DOWN)
            laila_viral_post = PostGen(VGroup(need_help, cleo_I), img=laila, name=TexGen(r'Laila\\Podlesny', font_sz=25, col=WHITE_G), date=TexGen(r'5:07 p.m.', font_sz=20, col=GRAY_G), answer=False).next_to(nov11, DOWN, buff=post_after_date_buff).to_edge(browser.get_edge_center(LEFT)).shift(post_buff*RIGHT)
            infos = TexGen(r'$\ldots$', col=BLACK_G, font_sz=25).next_to(cleo_I, DOWN).set_z_index(0.5)
            newTxt = VGroup(need_help, cleo_I, infos)
            intro_I = VGroup(laila_viral_post[0], laila_viral_post[1])
            intro_I.save_state()
            intro_I.scale(2).move_to(ORIGIN)
            star = TexGen(r'*', font_sz=50, col=RED_G).next_to(bar, buff=0.1)
            refs = TexGen(r'Sources/References\\in the video description', col=GRAY_G, font_sz=20).next_to(star, aligned_edge=UP, buff=-0.1)
            self.add(black_rect_up, black_rect_down)
            self.play(FadeIn(intro_I[0], run_time=0.5))
            self.play(DrawTxt(intro_I[1]))
            self.wait()
            self.play(FadeIn(browser, bar), Create(nov11), GrowFromCenter(laila_viral_post[2:6], rate_func=rush_from, run_time=0.3), Create(laila_viral_post[-1]), Restore(intro_I))
            self.play(TypeWithCursor(link_mathstack, cursor=cursor, leave_cursor_on=False))
            self.play(DrawTxt(star), DrawTxt(refs))
            self.wait()
            self.play(FadeOut(star, refs))
            self.wait()
            self.play(laila_viral_post[0].animate.stretch_to_fit_height(newTxt.height+0.4).move_to(laila_viral_post[0], aligned_edge=UP), DrawTxt(infos))
            cleo_viral_post = PostGen(Group(cleo_sol_laila, phi), img=cleo, name=TexGen(r'Cleo', font_sz=25, col=WHITE_G), date=TexGen(r'9:43 p.m.', font_sz=20, col=GRAY_G), answer=True).next_to(laila_viral_post, DOWN, buff=post_buff).to_edge(browser.get_edge_center(RIGHT)).shift(post_buff*LEFT)
            self.wait()
            self.play(Post(cleo_viral_post, answer=True))
            nov13 = TexGen(r'Nov 13, 2013', font_sz=20, col=GRAY_G).next_to(cleo_viral_post, DOWN, buff=post_buff).set_x(nov11.get_x())
            rons = ImageMobject('rons.png')
            rons.height = 1.7
            ron_post = PostGen(rons, img=ron, name=TexGen(r'Ron\\Gordon', font_sz=25, col=WHITE_G), date=TexGen(r'5:08 p.m.', font_sz=20, col=GRAY_G), answer=True, w_buff=0.2, h_buff=0.2).next_to(nov13, DOWN, buff=post_after_date_buff).to_edge(browser.get_edge_center(RIGHT)).shift(post_buff*LEFT)
            self.wait()
            self.play(Create(nov13))
            self.play(Post(ron_post))
            self.wait()
            self.play(Group(ron_post[0], ron_post[1]).animate.scale_to_fit_height(6.6).move_to(ron_post[0], aligned_edge=DR), FadeOut(laila_viral_post, cleo_viral_post, infos, nov11, nov13, run_time=0.4))
            self.wait()
            self.play(LaggedStart(Group(ron_post[0], ron_post[1]).animate.scale_to_fit_height(1.7).move_to(ron_post[0], aligned_edge=DR), FadeIn(laila_viral_post, cleo_viral_post, infos, nov11, nov13, run_time=0.4), lag_ratio=0.5))
            self.wait()
            pseudo_date = TexGen(r'$\ldots$', font_sz=20, col=GRAY_G).next_to(ron_post, DOWN, buff=post_buff).set_x(nov11.get_x())
            pseudo_question = TexGen(r'pseudo\\pseudo\\pseudopseudopseudopseudopseudopseudo', col=WHITE_G, font_sz=25)
            pseudo_answer = TexGen(r'pseudopseudopseudopseudo', col=WHITE_G, font_sz=25)
            pseudo_expl = TexGen(r'.............\\.............\\.............\\.............\\.............\\.............\\.............', col=WHITE_G, font_sz=25)
            pseudo_posts = Group()
            prev_date = pseudo_date
            for i in range(36):    
                pseudo_question_post = PostGen(deepcopy(pseudo_question), img=Square().set_fill(color=WHITE_G, opacity=1).set_stroke(width=0), name=TexGen(r'Pseudo', font_sz=25, col=USR_G), date=TexGen(r'$\ldots$', font_sz=20, col=GRAY_G), answer=False).next_to(prev_date, DOWN, buff=post_after_date_buff).to_edge(browser.get_edge_center(LEFT)).shift(post_buff*RIGHT)
                pseudo_cleo_post = PostGen(deepcopy(pseudo_answer), img=deepcopy(cleo), name=TexGen(r'Cleo', font_sz=25, col=WHITE_G), date=TexGen(r'$\ldots$', font_sz=20, col=GRAY_G), answer=True).next_to(pseudo_question_post, DOWN, buff=post_buff).to_edge(browser.get_edge_center(RIGHT)).shift(post_buff*LEFT)
                next_date = deepcopy(pseudo_date).next_to(pseudo_cleo_post, DOWN, buff=post_buff).set_x(nov11.get_x())
                pseudo_expl_post = PostGen(deepcopy(pseudo_expl), img=Square().set_fill(color=WHITE_G, opacity=1).set_stroke(width=0), name=TexGen(r'Pseudo', font_sz=25, col=USR_G), date=TexGen(r'$\ldots$', font_sz=20, col=GRAY_G), answer=True).next_to(next_date, DOWN, buff=post_after_date_buff).to_edge(browser.get_edge_center(RIGHT)).shift(post_buff*LEFT)
                pseudo_posts.add(prev_date, pseudo_question_post, pseudo_cleo_post, next_date, pseudo_expl_post)
                prev_date = deepcopy(pseudo_date).next_to(pseudo_expl_post, DOWN, buff=post_buff).set_x(nov11.get_x())       
            self.add(pseudo_posts)
            dec31 = TexGen(r'Dec 31, 2015', font_sz=20, col=GRAY_G).next_to(pseudo_posts[-1], DOWN, buff=post_buff).set_x(nov11.get_x())
            last_question = TexGen(r'I need to evaluate this integral:', col=BLACK_G, font_sz=25)
            oksana_I = TexGen(r'I=\int_0^{\pi/2}\arctan^2\!\left(\frac{\sin x}{\sqrt3+\cos x}\right)dx', isMath=True, font_sz=25, col=BLACK_G).next_to(last_question, DOWN)
            infos_cp = deepcopy(infos).next_to(oksana_I, DOWN)
            oksana_post = PostGen(VGroup(last_question, oksana_I, infos_cp), img=oksana, name=TexGen(r'Oksana\\Gimmel', font_sz=25, col=WHITE_G), date=TexGen(r'7:11 p.m.', font_sz=20, col=GRAY_G), answer=False).next_to(dec31, DOWN, buff=post_after_date_buff).to_edge(browser.get_edge_center(LEFT)).shift(post_buff*RIGHT)
            cleo_last_sol = TexGen(r'I=\frac\pi{20}\ln^23+\frac\pi4\operatorname{Li_2}\left(\tfrac13\right)-\frac15\operatorname{Ti}_3\left(\sqrt3\right)', isMath=True, font_sz=25, col=BLACK_G)
            cleo_last_post = PostGen(cleo_last_sol, img=deepcopy(cleo), name=TexGen(r'Cleo', font_sz=25, col=WHITE_G), date=TexGen(r'8:43 p.m.', font_sz=20, col=GRAY_G), answer=True).next_to(oksana_post, DOWN, buff=post_buff).to_edge(browser.get_edge_center(RIGHT)).shift(post_buff*LEFT)
            pseudo_posts.add(dec31, oksana_post, cleo_last_post)
            buff_obj = Dot(color=BLACK).move_to([10, 10, -10])
            e0 = ImageMobject('e0.png').move_to([0, 0, 0])
            e1 = ImageMobject('e1.png').move_to([-2.5, 1, 0])
            e2 = ImageMobject('e2.png').move_to([1.5, 1.5, 0])
            e3 = ImageMobject('e3.png').move_to([-2.5, -2.1, 0])
            e4 = ImageMobject('e4.png').move_to([2.5, -1, 0])
            e5 = ImageMobject('e5.png').move_to([0.4, 2.1, 0])
            e6 = ImageMobject('e6.png').move_to([0, -1.5, 0])
            e7 = ImageMobject('e7.png').move_to([-1.5, 1.5, 0])
            e8 = ImageMobject('e8.png').move_to([-3, -1, 0])
            e9 = ImageMobject('e9.png').move_to([2.4, 1, 0])
            emojis = Group(buff_obj, deepcopy(buff_obj), e0, e1, e2, e3, e4, e5, e6, e7, e8, e9)
            for e in emojis[2:]:
                e.height=1.8
            self.play(Group(pseudo_posts, laila_viral_post, infos, cleo_viral_post, ron_post, nov11, nov13).animate.shift((np.abs(dec31.get_y())+np.abs(nov11.get_y()))*UP), LaggedStart(*(GrowFromCenter(e, point_color=BROWSER_G[0], rate_func=there_and_back, run_time=2.1) for e in emojis), lag_ratio=0.2), run_time=15)
            
        def play_theories():
            self.play(GrowFromCenter(news, point_color=BLACK))
            self.wait()
            self.play(FadeOut(news))
            self.wait()
            cleo_tp = ImageMobject('cleo_tp.webp')
            cleo_tp.height = 1.5
            self.play(FadeIn(cleo_tp.shift(2.8*UP)))
            self.wait()
            genius = TexGen(r'Genius', font_sz=50, col=WHITE_G).next_to(cleo_tp, DOWN)
            troll_txt = TexGen(r'Troll', font_sz=50, col=WHITE_G).move_to(genius)
            trolls_txt = TexGen(r'Trolls', font_sz=50, col=WHITE_G).move_to(genius)
            ai_txt = TexGen(r'AI', font_sz=50, col=WHITE_G).move_to(genius)
            prof = TexGen(r'Prof', font_sz=50, col=WHITE_G).move_to(genius)
            spy = TexGen(r'Spy', font_sz=50, col=WHITE_G).move_to(genius)
            self.play(DrawTxt(genius))
            tao.next_to(genius, 1.5*DOWN).shift(3*RIGHT)
            ramanujan.next_to(genius, 1.5*DOWN).shift(3*LEFT)
            tao_name = TexGen(r'Terence\\Tao', isMath=False, font_sz=30).next_to(tao, DOWN, buff=0.2)
            ramanujan_name = TexGen(r'Srinivasa\\Ramanujan\\(1887--1920)', isMath=False, font_sz=30).next_to(ramanujan, DOWN, buff=0.2)
            self.wait()
            self.play(BounceIn(ramanujan), DrawTxt(ramanujan_name))
            self.wait()
            self.play(BounceIn(tao), DrawTxt(tao_name))
            self.wait()
            self.play(BounceIn(troll.next_to(genius, 1.5*DOWN)), ReplacementTransform(genius, troll_txt), Group(tao, tao_name).animate.shift(10*RIGHT), Group(ramanujan, ramanujan_name).animate.shift(10*LEFT))
            self.wait()
            troll_r1 = deepcopy(troll).next_to(troll, RIGHT, buff=-1.3).scale_to_fit_height(2.2).set_z_index(-0.01)
            troll_r2 = deepcopy(troll).next_to(troll_r1, RIGHT, buff=-1.3).scale_to_fit_height(1.4).set_z_index(-0.02)
            troll_r3 = deepcopy(troll).next_to(troll_r2, RIGHT, buff=-1.3).scale_to_fit_height(0.6).set_z_index(-0.03)
            troll_l1 = deepcopy(troll).next_to(troll, LEFT, buff=-1.3).scale_to_fit_height(2.2).set_z_index(-0.01)
            troll_l2 = deepcopy(troll).next_to(troll_l1, LEFT, buff=-1.3).scale_to_fit_height(1.4).set_z_index(-0.02)
            troll_l3 = deepcopy(troll).next_to(troll_l2, LEFT, buff=-1.3).scale_to_fit_height(0.6).set_z_index(-0.03)
            trolls = Group(troll_r1, troll_l1, troll_r2, troll_l2, troll_r3, troll_l3)
            self.play(BounceIn(trolls), ReplacementTransform(troll_txt, trolls_txt, run_time=0.5))
            self.wait()
            fade_rect = Rectangle(width=14, height=3.2).move_to(troll).set_fill(BLACK, opacity=1).set_stroke(width=0)
            self.play(FadeIn(fade_rect))
            self.remove(troll, *trolls)
            self.remove(fade_rect)
            in2013 = TexGen(r'in 2013?', isMath=False, font_sz=30).next_to(ai, DOWN, buff=0.2)
            stud1 = PersonGen('S')
            stud2 = PersonGen('S').next_to(stud1)
            stud3 = PersonGen('S').next_to(stud2)
            stud4 = PersonGen('S').next_to(stud3)
            stud1.height = cleo_tp.height
            stud2.height = cleo_tp.height
            stud3.height = cleo_tp.height
            stud4.height = cleo_tp.height
            studs = VGroup(stud1, stud2, stud3, stud4).next_to(genius, 1.5*DOWN)
            self.play(BounceIn(ai.move_to(troll)), ReplacementTransform(trolls_txt, ai_txt, run_time=0.5))
            self.wait()
            self.play(DrawTxt(in2013.next_to(ai, DOWN, buff=0.2)))
            self.wait()
            self.play(FadeOut(ai, in2013), ReplacementTransform(ai_txt, prof))
            self.play(BounceIn(studs))
            self.wait()
            spy_img = ImageMobject('glas.png').move_to(cleo_tp).shift(0.17*UP+0.02*RIGHT)
            spy_img.height=0.5
            self.play(ReplacementTransform(prof, spy), FadeIn(spy_img), FadeIn(fade_rect))

        def play_timeline():
            self.play(Create(may2024))
            self.wait()
            self.play(BounceIn([energysens, rect_around_energy]), DrawTxt(energyS))
            self.wait()
            self.play(Create(sep2024))
            self.play(BounceIn([evil_dog, rect_around_dog]), DrawTxt(evilS))
            self.play(FadeIn(Group(evil_browser, evil_bar), target_position=[0, evilS.get_y(), 0]))
            self.play(TypeWithCursor(link_investigate, cursor=cursor.next_to(link_investigate, buff=-0.1), leave_cursor_on=False))
            self.wait()
            evil_browser_cp = deepcopy(evil_browser).set_z_index(10)
            evil_bar_cp = deepcopy(evil_bar).set_z_index(10)
            bar_cp = deepcopy(bar).set_z_index(10)
            self.play(ReplacementTransform(evil_browser, browser), ReplacementTransform(evil_bar, bar_cp), link_investigate.animate.move_to(bar).set_z_index(10))
            self.wait()
            self.play(DrawTxt(evolution))
            self.play(GrowFromCenter(cleo_profile, point_color=BROWSER_G[0]))
            self.wait()
            self.play(GrowFromEdge(bio_rect, edge=UL, point_color=BROWSER_G[0]))
            self.play(DrawTxt(bio))
            self.wait()
            gauss_q = TexGen(r'\raggedright\textit{``No self-respecting architect leaves the scaffolding in place\\after completing the building."} — Gauss', font_sz=26, stroke_w=0.5, col=BLACK_G).next_to(bio, DOWN).align_to(bio_rect, LEFT).shift(0.2*RIGHT)
            rama_q = TexGen(r'\raggedright\textit{``While asleep, I had an unusual experience. There was a red\\screen formed by flowing blood, as it were. I was observing it.\\Suddenly a hand began to write on the screen. I became all\\attention. That hand wrote a number of elliptic integrals.\\They stuck to my mind. As soon as I woke up, I committed\\them to writing."} — Ramanujan', font_sz=26, stroke_w=0.5, col=BLACK_G).next_to(gauss_q, DOWN, aligned_edge=LEFT)
            cleo_q = TexGen(r'\raggedright Remember, you are not locked into a single axiom system.\\You may invent your own, whenever you wish — just use\\your intuition and imagination.', font_sz=26, stroke_w=0.5, col=BLACK_G).next_to(rama_q, DOWN, aligned_edge=LEFT)
            cleo_q2 = TexGen(r'\raggedright Do not take my posts and comments too seriously.', font_sz=26, stroke_w=0.5, col=BLACK_G).next_to(cleo_q, 2.5*DOWN, aligned_edge=LEFT)
            smiley = TexGen(r'$\hspace{.1in}\stackrel{\checkmark\checkmark}{\stackrel\wr\smile}$', font_sz=30, col=BLACK_G).next_to(cleo_q2, aligned_edge=DOWN)
            self.play(DrawTxt(gauss_q))
            self.wait()
            self.play(DrawTxt(rama_q))
            self.wait()
            self.play(DrawTxt(cleo_q))
            self.wait()
            self.play(DrawTxt(cleo_q2))
            self.wait()
            self.play(DrawTxt(smiley))
            self.wait()
            self.play(FadeOut(cleo_q2, smiley))
            self.wait()
            bitcoin = TexGen(r'\raggedright Do you like my answers? If you wish, you can send me some\\bitcoins as a token of your appreciation :-) Thank you!', font_sz=26, stroke_w=0.5, col=BLACK_G).next_to(bio, DOWN).align_to(bio_rect, LEFT).shift(0.2*RIGHT)
            self.play(FadeOut(gauss_q, rama_q, cleo_q))
            self.play(DrawTxt(bitcoin))
            medical = TexGen(r"\raggedright My real name is Cleo, I'm female. I have a medical condition\\that makes it very difficult for me to engage in conversations,\\or post long answers, sorry for that. I like math and do my\\best to be useful at this site, although I realize my answers\\might be not useful for everyone.", font_sz=26, stroke_w=0.5, col=BLACK_G).next_to(bio, DOWN).align_to(bio_rect, LEFT).shift(0.2*RIGHT)
            self.wait()
            self.play(FadeOut(bitcoin))
            self.play(DrawTxt(medical))
            self.wait()
            self.add(analysis)
            self.add(black_rect_down, black_rect_up)
            self.play(Group(evolution, cleo, cleo_name, bio_rect, bio, medical, analysis, rect_around_cleo).animate.shift(7.5*UP))
            self.wait()
            self.play(GrowFromCenter(plot_group, point_color=BROWSER_G[0]))
            self.wait()
            self.play(Create(highlight_rect))
            self.wait()
            self.play(Create(left_line), Create(right_line))
            self.wait()
            self.play(Group(analysis, plot_group, highlight_rect, left_line, right_line).animate.shift(7.5*UP))
            self.play(GrowFromCenter(cleo_usr, point_color=BROWSER_G[0]))
            self.play(GrowFromCenter(usr_of_interest, point_color=BROWSER_G[0]))
            self.wait()
            browser_cp = deepcopy(browser).set_z_index(10)
            bar_cp2 = deepcopy(bar_cp).set_z_index(10)
            usr_of_interest_cp = deepcopy(usr_of_interest).set_z_index(10)
            cleo_usr_cp = deepcopy(cleo_usr).set_z_index(10)
            self.play(ReplacementTransform(browser, evil_browser_cp), ReplacementTransform(bar_cp, evil_bar_cp), link_investigate.animate.move_to(evil_bar_cp).set_z_index(10), Group(cleo_usr, usr_of_interest).animate.stretch_to_fit_height(0.1).stretch_to_fit_width(4).shift(UP).fade(darkness=1))
            self.wait()
            self.play(Create(jan2025))
            self.play(BounceIn([joe, rect_around_joe]), DrawTxt(joe_name))   
            self.play(FadeIn(vid, target_position=[0, joe_name.get_y()-0.7, 0]))   
            self.wait()      
            self.play(Create(feb2025))
            self.play(DrawTxt(salt))
            self.wait()
            self.play(ReplacementTransform(evil_browser_cp, browser_cp), ReplacementTransform(evil_bar_cp, bar_cp2), link_investigate.animate.move_to(bar_cp2).set_z_index(10), GrowFromCenter(Group(cleo_usr_cp, usr_of_interest_cp), point_color=BROWSER_G[0]))

        def play_identity():
            self.add(browser, bar, cleo_usr, usr_of_interest, link_investigate.move_to(bar))
            nov11 = TexGen(r'Nov 11, 2013', font_sz=20, col=GRAY_G).next_to(bar, DOWN)
            need_help = TexGen(r'I need help with this integral:', col=BLACK_G, font_sz=25)
            cleo_I = TexGen(r'I = \int_{-1}^{1} \frac{1}{x}\sqrt{\frac{1+x}{1-x}}\ln\!\left(\frac{2x^{2}+2x+1}{2x^{2}-2x+1}\right)\,dx', isMath=True, font_sz=25, col=BLACK_G).next_to(need_help, DOWN)
            infos = TexGen(r'$\ldots$', col=BLACK_G, font_sz=25).next_to(cleo_I, DOWN).set_z_index(0.5)
            cleo_sol_laila = TexGen(r'I = 4 \pi \textup{arccot}\sqrt{\phantom{\phi}}', isMath=True, font_sz=25, col=BLACK_G)
            phi = TexGen(r'\phi', isMath=True, font_sz=25, col=LINK_G).move_to(cleo_sol_laila, aligned_edge=RIGHT).set_z_index(1).shift(0.02*DOWN)
            laila_viral_post = PostGen(VGroup(need_help, cleo_I, infos), img=laila, name=TexGen(r'Laila\\Podlesny', font_sz=25, col=WHITE_G), date=TexGen(r'5:07 p.m.', font_sz=20, col=GRAY_G), answer=False).next_to(nov11, DOWN, buff=post_after_date_buff).to_edge(browser.get_edge_center(LEFT)).shift(post_buff*RIGHT)
            cleo_viral_post = PostGen(Group(cleo_sol_laila, phi), img=cleo, name=TexGen(r'Cleo', font_sz=25, col=WHITE_G), date=TexGen(r'9:43 p.m.', font_sz=20, col=GRAY_G), answer=True).next_to(laila_viral_post, DOWN, buff=post_buff).to_edge(browser.get_edge_center(RIGHT)).shift(post_buff*LEFT)
            laila_pos = Group(*laila_viral_post[2:6]).get_center()
            cleo_pos = Group(*cleo_viral_post[2:6]).get_center()
            laila_usr = Group(*laila_viral_post[2:6]).move_to(usr_of_interest[0], aligned_edge=LEFT)
            self.play(ReplacementTransform(usr_of_interest[0][0], laila_usr[0]), ReplacementTransform(usr_of_interest[0][-1], laila_usr[3]), FadeIn(laila_usr[1], laila_usr[2]))
            self.remove(usr_of_interest[0])
            self.play(laila_usr.animate.move_to(laila_pos), FadeOut(usr_of_interest[1:], run_time=0.5), cleo_usr.animate.move_to(cleo_pos), LaggedStart(UntypeWithCursor(link_investigate, cursor=cursor.next_to(link_investigate, buff=-0.1).set_z_index(10), leave_cursor_on=True), TypeWithCursor(link_mathstack, cursor=cursor.set_z_index(10), leave_cursor_on=False), lag_ratio=1, run_time=1.2))
            self.play(Create(cleo_viral_post[-1]), GrowFromPoint(Group(*cleo_viral_post[0:2]), cleo_pos-[1, 0, 0]),
                      Create(laila_viral_post[-1]), GrowFromPoint(Group(*laila_viral_post[0:2]), laila_pos-[1, 0, 0]), Create(nov11))
            self.wait()
            laila_new_img = deepcopy(laila)
            laila_new_img.height = 1.05
            rect_around_laila = RectAroundImage(laila_new_img, col1=BROWSER_G, col2=BROWSER_G).set_z_index(10)
            laila_profile = Group(laila_new_img, rect_around_laila).move_to(laila_usr, aligned_edge=UL)
            self.play(laila_usr[0].animate.set_color(BROWSER_G), ReplacementTransform(laila_usr[2], laila_profile[-1]), laila_usr[1].animate.move_to(laila_new_img).scale_to_fit_height(1.05), 
                      FadeOut(cleo_usr, nov11, cleo_usr, laila_viral_post[0:2], cleo_viral_post[0:2], laila_viral_post[-1], cleo_viral_post[-1]), laila_usr[3].animate.next_to(laila_profile[-1], DOWN, buff=0.1))
            bio_rect.next_to(rect_around_laila[0], aligned_edge=UP, buff=0.15).stretch_to_fit_width(7.4)
            self.remove(laila_usr[0])
            self.play(GrowFromEdge(bio_rect, edge=UL, point_color=BROWSER_G[0]))
            self.play(DrawTxt(bio.move_to(bio_rect, aligned_edge=UP).shift(0.2*DOWN)))
            self.wait()
            laila_mail = TexGen(r'laila.podlesny@gmail.com', col=BLACK_G, font_sz=26, stroke_w=0.5).next_to(bio, DOWN)
            self.play(DrawTxt(laila_mail))
            self.wait()
            d_arr = TexGen(r'\downarrow', col=RED_G, isMath=True, font_sz=80).next_to(laila_mail, DOWN)
            dont = TexGen(r"(Don't do this!)", col=RED_G, font_sz=26).next_to(d_arr).shift(0.1*UP)
            self.play(DrawTxt(d_arr))
            self.play(DrawTxt(dont))
            rec_mail = TexGen(r'v.res********@gmail.com', col=RED_G, font_sz=26, stroke_w=0.5).next_to(d_arr, DOWN)
            v_bio = TexGen(r'Software dev, with background in theoretical physics.', col=BLACK_G, font_sz=26, stroke_w=0.5).next_to(bio, DOWN)
            books = ImageMobject(r'books.png')
            pc = ImageMobject(r'pc.png')
            stars = ImageMobject(r'stars.png')
            books.height = 0.2
            pc.height = 0.2
            stars.height = 0.2
            pc.next_to(books, buff=0.1)
            emoji_group = Group(books, pc, stars.next_to(pc, buff=0.1)).next_to(v_bio, DOWN, buff=0.2)
            v_mail = TexGen(r'v.reshetnikov@gmail.com', col=BLACK_G, font_sz=26, stroke_w=0.5).next_to(emoji_group, DOWN).scale_to_fit_width(rec_mail.width)
            self.wait()
            self.play(DrawTxt(rec_mail))
            self.wait()
            vladimir.move_to(laila_usr[1]).set_z_index(10)
            rect_around_v = RectAroundImage(vladimir, col1=BROWSER_G, col2=BROWSER_G).set_z_index(10)
            v_name = TexGen(r'Vladimir\\Reshetnikov', font_sz=24, col=WHITE_G).next_to(laila_profile[-1], DOWN, buff=0.1)
            self.play(FadeOut(dont, laila_mail, d_arr))
            self.play(DrawTxt(v_bio), DrawTxt(v_mail), GrowFromCenter(books, point_color=WHITE), GrowFromCenter(pc, point_color=WHITE), GrowFromCenter(stars, point_color=WHITE),
                      FadeIn(vladimir), FadeIn(rect_around_v, run_time=0.1), ReplacementTransform(laila_usr[3], v_name))
            self.wait()
            self.remove(laila_usr[1], laila_usr[2])
            self.play(FadeOut(vladimir, rect_around_v.set_z_index(10), v_name, bio_rect, bio, v_bio, rec_mail, emoji_group, v_mail, run_time=0.4), UntypeWithCursor(link_mathstack, cursor=cursor.next_to(link_mathstack, buff=-0.1).set_z_index(10), leave_cursor_on=True, run_time=0.8))
            self.play(TypeWithCursor(link_investigate, cursor=cursor.next_to(link_investigate, buff=-0.1).set_z_index(10), leave_cursor_on=False), run_time=0.8)
            self.play(DrawTxt(analysis.shift(7.5*UP)), GrowFromCenter(plot_group, point_color=BROWSER_G[0]), GrowFromCenter(highlight_rect, point_color=BROWSER_G[0]), GrowFromCenter(left_line, point_color=BROWSER_G[0]), GrowFromCenter(right_line, point_color=BROWSER_G[0]))
            self.wait()
            highlight_rect_cp = deepcopy(highlight_rect).shift(3.09*UP)
            self.play(FadeIn(highlight_rect_cp, target_position=highlight_rect))
            self.wait()
            timeline = Group(may2024, energyS, energysens, rect_around_energy, sep2024, evilS, evil_dog, rect_around_dog, jan2025, joe_name, joe, rect_around_joe, vid, rect_around_vid, feb2025, salt).set_z_index(-0.1)
            self.add(timeline)
            browser_cp = deepcopy(browser).set_z_index(10)
            bar_cp = deepcopy(bar).set_z_index(10)
            self.play(Group(analysis, highlight_rect, highlight_rect_cp, plot_group, left_line, right_line).animate.stretch_to_fit_height(0.1).stretch_to_fit_width(4).shift(UP).fade(darkness=1),
                      ReplacementTransform(browser, evil_browser), ReplacementTransform(bar, evil_bar), link_investigate.animate.move_to(evil_bar).set_z_index(10))
            confirm = TexGen(r'\ding{52}', font_sz=60).next_to(salt, buff=0.2).set_z_index(-1)
            self.wait()
            self.play(DrawTxt(confirm))
            self.wait()
            cleo_usr.move_to(browser_cp).set_z_index(10)
            laila_viral_post = PostGen(VGroup(need_help), img=laila, name=TexGen(r'Laila\\Podlesny', font_sz=25, col=WHITE_G), date=TexGen(r'5:07 p.m.', font_sz=20, col=GRAY_G), answer=False)
            oct5 = TexGen(r'Oct 5, 2013', font_sz=20, col=GRAY_G).next_to(bar_cp, DOWN).set_z_index(10)
            v_hobby = TexGen(r'\raggedright My hobby is to seach for closed forms of integrals\\that cannot be evaluated by modern CAS like\\\textit{Maple} or \textit{Mathematica}.', col=BLACK_G, font_sz=25)
            infos2 = deepcopy(infos).next_to(v_hobby, DOWN)
            v_asks = TexGen(r"\raggedright I am asking for your advice, what is the best way\\to post my conjectures, without saying too much\\words for introductions, but to attract people's\\attention and make the problem interesing for\\them?", col=BLACK_G, font_sz=25).next_to(infos2, DOWN).align_to(v_hobby, LEFT)
            v_post = PostGen(VGroup(v_hobby, infos2, v_asks), img=vladimir, name=TexGen(r'Vladimir\\Reshetnikov', font_sz=25, col=WHITE_G), date=TexGen(r'6:10 p.m.', font_sz=20, col=GRAY_G), answer=False, w_buff=0.9).next_to(oct5, DOWN, buff=post_after_date_buff).to_edge(browser_cp.get_edge_center(LEFT)).shift(post_buff*RIGHT).set_z_index(10)
            v_post_usr_pos = Group(v_post[2:6]).get_center()
            usr_of_interest.add(laila_viral_post[2:6].next_to(cleo_usr, UL).set_z_index(10))
            v_post[2:6].set_z_index(10)
            usr_of_interest.add(v_post[2:6].next_to(cleo_usr, UR))
            self.play(ReplacementTransform(evil_browser, browser_cp), ReplacementTransform(evil_bar, bar_cp), link_investigate.animate.move_to(bar_cp).set_z_index(10), GrowFromCenter(Group(cleo_usr, usr_of_interest[2:].set_z_index(10)), point_color=BROWSER_G[0]))
            self.wait()
            oleg_post = PostGen(VGroup(deepcopy(infos)), img=oleg, name=TexGen(r'OlegK', font_sz=25, col=WHITE_G), date=TexGen(r'7:11 p.m.', font_sz=20, col=GRAY_G), answer=False)
            oleg_usr = Group(*oleg_post[2:6]).move_to(usr_of_interest[2], aligned_edge=LEFT).set_z_index(10)
            oksana_post = PostGen(VGroup(deepcopy(infos)), img=oksana, name=TexGen(r'Oksana\\Gimmel', font_sz=25, col=WHITE_G), date=TexGen(r'7:11 p.m.', font_sz=20, col=GRAY_G), answer=False)
            oksana_usr = Group(*oksana_post[2:6]).move_to(usr_of_interest[3], aligned_edge=LEFT).set_z_index(10)
            self.play(ReplacementTransform(usr_of_interest[2][0], oleg_usr[0]), ReplacementTransform(usr_of_interest[2][-1], oleg_usr[3]), FadeIn(oleg_usr[1], oleg_usr[2]))
            self.play(ReplacementTransform(usr_of_interest[3][0], oksana_usr[0]), ReplacementTransform(usr_of_interest[3][-1], oksana_usr[3]), FadeIn(oksana_usr[1], oksana_usr[2]))
            self.wait()
            self.remove(usr_of_interest[2][1], usr_of_interest[2][2], usr_of_interest[3][1], usr_of_interest[3][2])
            self.play(usr_of_interest[4].animate.move_to(v_post[2:6]).fade(darkness=1).scale(0.5),
                      oleg_usr.animate.move_to(v_post[2:6]).fade(darkness=1).scale(0.5),
                      cleo_usr.animate.move_to(v_post[2:6]).fade(darkness=1).scale(0.5),
                      oksana_usr.animate.move_to(v_post[2:6]).fade(darkness=1).scale(0.5))
            self.wait()
            troll_sq = ImageMobject('troll_sq.png')
            troll_sq.scale_to_fit_width(0.8).move_to(v_post[3]).set_z_index(10)
            rect_around_troll = RectAroundImage(troll_sq, col1=USR_G, col2=USR_G, additionals=6).set_z_index(10)
            self.play(FadeIn(troll_sq, rect_around_troll))
            self.wait()
            self.play(FadeOut(troll_sq, rect_around_troll, run_time=0.4), UntypeWithCursor(link_investigate, cursor=cursor.next_to(link_investigate, buff=-0.1).set_z_index(10), leave_cursor_on=True, run_time=0.8))
            self.play(v_post[2:6].animate.move_to(v_post_usr_pos), Create(oct5), TypeWithCursor(link_mathstack_meta, cursor=cursor.next_to(link_investigate, buff=-0.1).set_z_index(10), leave_cursor_on=False, run_time=0.8))
            browser_cp.set_z_index(9.99)
            v_post[0:2].set_z_index(10)
            v_post[2:6].set_z_index(10.01)
            self.play(Create(v_post[-1]), GrowFromPoint(Group(*v_post[0:2]), v_post_usr_pos+[1, 0, 0]))
            self.wait()
            browser_cp.set_z_index(5)
            bar_cp.set_z_index(10.02)
            link_mathstack_meta.set_z_index(10.02)
            nov20 = TexGen(r'Nov 20, 2013', font_sz=20, col=GRAY_G).move_to(oct5).set_z_index(11)
            ron_asks = TexGen(r'Are answers that have no explanations useful?', col=BLACK_G, font_sz=25)
            infos3 = deepcopy(infos).next_to(ron_asks, DOWN)
            ron_post = PostGen(VGroup(ron_asks, infos3), img=ron, name=TexGen(r'Ron\\Gordon', font_sz=25, col=WHITE_G), date=TexGen(r'3:27 p.m.', font_sz=20, col=GRAY_G), answer=False, w_buff=0.9).next_to(nov20, DOWN, buff=post_after_date_buff).to_edge(browser_cp.get_edge_center(LEFT)).shift(post_buff*RIGHT).set_z_index(11)
            self.add(black_rect_down.set_z_index(11), black_rect_up.set_z_index(11))
            ron_post[2:6].set_z_index(12)
            self.play(Group(oct5, v_post).animate.shift(4.5*UP))
            self.play(Create(nov20))
            self.play(Post(ron_post, answer=False))
            self.wait()
            nov21 = TexGen(r'Nov 21, 2013', font_sz=20, col=GRAY_G).next_to(ron_post, DOWN).set_z_index(11).set_x(0)
            infos4 = deepcopy(infos)
            v_answ = TexGen(r'\raggedright They challenge other users to look for a proof,\\that they might not even try otherwise', col=BLACK_G, font_sz=25).next_to(infos4, DOWN)
            infos5 = deepcopy(infos).next_to(v_answ, DOWN)
            v_answ_post = PostGen(VGroup(infos4, v_answ, infos5), img=deepcopy(vladimir), name=TexGen(r'Vladimir\\Reshetnikov', font_sz=25, col=WHITE_G), date=TexGen(r'9:04 p.m.', font_sz=20, col=GRAY_G), answer=True, w_buff=0.9).next_to(nov21, DOWN, buff=post_after_date_buff).to_edge(browser_cp.get_edge_center(RIGHT)).shift(post_buff*LEFT).set_z_index(11)
            v_answ_post[2:6].set_z_index(12)
            self.play(Create(nov21))
            self.play(Post(v_answ_post))    


        # GLOBALS
        post_after_date_buff = 0.1
        post_buff = 0.3
        browser= RoundedRectangle(corner_radius=0.25, width=9.5, height=7.5).set_fill(BROWSER_G, opacity=1).set_stroke(width=0)
        bar = RoundedRectangle(corner_radius=0.25, width=9.5, height=0.5).set_fill(BAR_G, opacity=1).set_stroke(width=0).move_to(browser, aligned_edge=UP).set_z_index(10)
        black_rect_up = Rectangle(width=bar.width, height=5).set_fill(color=BLACK, opacity=1).set_stroke(color=BLACK).next_to(bar, UP, buff=0).set_z_index(10)
        black_rect_down = Rectangle(width=bar.width, height=5).set_fill(color=BLACK, opacity=1).set_stroke(color=BLACK).next_to(browser, DOWN, buff=0).set_z_index(10)
        laila = ImageMobject('laila.jpeg')
        cleo = ImageMobject('cleo.png')
        ron = ImageMobject('ron.jpg')
        oksana = ImageMobject('oksana.jpg')
        oleg = ImageMobject('oleg.jpeg')
        link_mathstack = Text('math.stackexchange.com/...', font_size=100, font='cmuntx').scale(0.17).move_to(bar).set_z_index(10)
        link_mathstack_meta = Text('math.meta.stackexchange.com/...', font_size=100, font='cmuntx').scale(0.17).move_to(bar).set_z_index(10)
        cursor = Line(start=ORIGIN, end=ORIGIN+[0, 0.25, 0]).next_to(link_mathstack, buff=-0.1)
        news = ImageMobject('news.png')
        news.height = 5
        ramanujan = ImageMobject(r'ramanujan.png')
        ramanujan.height = 3
        tao = ImageMobject(r'tao.png')
        tao.height = 3
        troll = ImageMobject(r'troll.png')
        troll.height = 3
        ai = ImageMobject(r'ai.png')
        ai.height = 3
        energysens = ImageMobject('energysens.png')
        energysens.height = 0.6
        evil_dog = ImageMobject('evil_dog.png')
        evil_dog.height = 0.6
        joe = ImageMobject('joe.jpg')
        joe.height = 0.6
        may2024 = TexGen(r'May 2024', col=GRAY_G, font_sz=30).shift(3.5*UP)
        rect_around_energy = RectAroundImage(energysens, col1=BLACK_G, col2=BLACK_G)
        energyS = TexGen(r'EnergySensitive7834 $\rightarrow$ Reddit Post', font_sz=40).next_to(rect_around_energy, buff=0.06).shift(0.05*DOWN)
        energy_usr = Group(energysens, rect_around_energy, energyS).next_to(may2024, DOWN, buff=0)
        sep2024 = TexGen(r'Sep 2024', col=GRAY_G, font_sz=30).next_to(energy_usr, DOWN, buff=0.2)
        rect_around_dog = RectAroundImage(evil_dog, col1=BLACK_G, col2=BLACK_G)
        evilS = TexGen(r'EvilScientist311 $\rightarrow$ Investigation Page', font_sz=40).next_to(rect_around_dog, buff=0.06).shift(0.05*DOWN)
        evil_usr = Group(evil_dog, rect_around_dog, evilS).next_to(sep2024, DOWN, buff=0)
        evil_browser= RoundedRectangle(corner_radius=0.25, width=5, height=0.5).set_fill(BROWSER_G, opacity=1).set_stroke(width=0)
        evil_bar = RoundedRectangle(corner_radius=0.25, width=5, height=0.5).set_fill(BAR_G, opacity=1).set_stroke(width=0).move_to(browser, aligned_edge=UP).set_z_index(10)
        evil_bar.move_to(evil_browser, aligned_edge=UP).set_z_index(10)
        Group(evil_browser, evil_bar).next_to(evil_usr, DOWN, buff=0.1).set_x(0)
        link_investigate = Text('cleoinvestigation.notion.site', font_size=100, font='cmuntx').scale(0.17).move_to(evil_bar).set_z_index(10)
        jan2025 = TexGen(r'Jan 2025', col=GRAY_G, font_sz=30).next_to(evil_bar, DOWN, buff=0.3)
        rect_around_joe = RectAroundImage(joe, col1=BLACK_G, col2=BLACK_G)
        joe_name = TexGen(r'Joe McCann $\rightarrow$ YouTube Video', font_sz=40).next_to(rect_around_joe, buff=0.06).shift(0.05*DOWN)
        joe_usr = Group(joe, rect_around_joe, joe_name).next_to(jan2025, DOWN, buff=0)
        yt_vid = ImageMobject('thumb.png')
        yt_vid.height = 1.5
        rect_around_vid = RectAroundImage(yt_vid, col1=YT_G, col2=YT_G, additionals=5)
        vid = Group(yt_vid, rect_around_vid).next_to(rect_around_joe, DOWN, buff=0.1).set_x(0)
        feb2025 = TexGen(r'Feb 2025', col=GRAY_G, font_sz=30).next_to(vid, DOWN, buff=0.4)
        salt = TexGen(r'Salt $\rightarrow$ Identity revealed', font_sz=40).next_to(feb2025, DOWN, buff=0.2)
        evolution = TexGen(r"The Evolution of Cleo's Profiles", font_sz=30).next_to(bar, DOWN)
        cleo.height = 1.05
        rect_around_cleo = RectAroundImage(cleo, col1=BROWSER_G, col2=BROWSER_G)
        cleo_name = TexGen(r"Cleo", font_sz=30).next_to(rect_around_cleo, DOWN, buff=0.1)
        cleo_profile = Group(cleo, rect_around_cleo, cleo_name).next_to(evolution, DOWN, buff=0.4).align_to(browser, LEFT).shift(0.2*RIGHT)
        vladimir = ImageMobject('vladimir.png')
        vladimir.height = 1.05
        bio_rect = RoundedRectangle(corner_radius=0.25, width=9.75-3*0.3-rect_around_cleo.width, height=5.8).set_stroke(width=0).set_fill(WHITE_G, opacity=1).next_to(rect_around_cleo[0], aligned_edge=UP, buff=0.25)
        bio = TexGen(r"Bio", font_sz=30, col=BLACK_G).move_to(bio_rect, aligned_edge=UP).shift(0.2*DOWN)
        analysis = TexGen(r"Data Analysis", font_sz=30).next_to(bar, DOWN).shift(7.5*DOWN)
        plot = ImageMobject('plot.webp')
        plot.height = 6
        rect_around_plot  = RectAroundImage(plot, col1=BROWSER_G, col2=BROWSER_G)
        plot_group = Group(plot, rect_around_plot).next_to(analysis, DOWN, buff=0.15).shift(7.5*UP)
        highlight_rect = RoundedRectangle(corner_radius=0.1, width=1.5, height=0.22).set_stroke(width=5.5, color=MAG_G).move_to([-1.25, -2.57, 0]).set_z_index(4)
        left_line = DashedLine(start=highlight_rect.get_edge_center(LEFT), end=highlight_rect.get_edge_center(LEFT)+[0, 5.1, 0], dash_length=0.13).set_stroke(width=4, color=MAG_G).shift(0.33*DOWN).set_z_index(3)
        right_line = DashedLine(start=highlight_rect.get_edge_center(RIGHT), end=highlight_rect.get_edge_center(RIGHT)+[0, 5.1, 0], dash_length=0.13).set_stroke(width=4, color=MAG_G).shift(0.33*DOWN).set_z_index(3)
        cleo_n = TexGen(r'Cleo', font_sz=25, col=WHITE_G)     
        cleo_cp = deepcopy(cleo).scale_to_fit_width(0.8).set_z_index(1)
        cleo_img_rects = RectAroundImage(img=cleo_cp, col1=USR_G, col2=USR_G, additionals=6).set_z_index(1)
        cleo_n.next_to(cleo_img_rects, buff=0.08)
        user_container = RoundedRectangle(corner_radius=0.2, width=Group(cleo_img_rects, cleo_n).width+0.25, height=Group(cleo_img_rects, cleo_n).height+0.06).set_fill(USR_G, opacity=1).set_stroke(width=0).move_to(Group(cleo_img_rects, cleo_n)).shift(0.09*RIGHT) 
        cleo_usr = Group(user_container, cleo_cp, cleo_img_rects, cleo_n).move_to(browser)
        usr_of_interest = Group()
        for i in range(4):
            pseudo_img = Square().set_fill(color=WHITE_G, opacity=1).set_stroke(width=0)  
            cleo_n = TexGen(r'User of\\Interest', font_sz=25, col=WHITE_G)     
            pseudo_img.scale_to_fit_width(0.8).set_z_index(1)
            cleo_img_rects = RectAroundImage(img=pseudo_img, col1=USR_G, col2=USR_G, additionals=6).set_z_index(1)
            cleo_n.next_to(cleo_img_rects, buff=0.08)
            user_container = RoundedRectangle(corner_radius=0.2, width=Group(cleo_img_rects, cleo_n).width+0.25, height=Group(cleo_img_rects, cleo_n).height+0.06).set_fill(USR_G, opacity=1).set_stroke(width=0).move_to(Group(cleo_img_rects, cleo_n)).shift(0.09*RIGHT) 
            usr_of_interest.add(VGroup(user_container, pseudo_img, cleo_img_rects, cleo_n))
        usr_of_interest[0].next_to(cleo_usr, UL)
        usr_of_interest[1].next_to(cleo_usr, UR)
        usr_of_interest[2].next_to(cleo_usr, DL)
        usr_of_interest[3].next_to(cleo_usr, DR)




        # ANIMATE
        self.wait()
        play_intro()
        play_theories()
        play_timeline()
        play_identity()
        self.wait()
