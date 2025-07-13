from telegram import Update, Dice
from telegram.ext import CommandHandler, CallbackContext
from tg_bot import dispatcher
import random
import time
from collections import defaultdict
from tg_bot.modules.helper_funcs.chat_status import is_privileged_user

response_flavors = [
    ("chill",
     lambda x, p, v: f"*{x}* is *{p}%* {v}, just vibin' like a pro! 😎"),
    (
        "savage",
        lambda x, p, v:
        f"Whoa, *{x}* just got SLAMMED with *{p}%* {v}! Take that, normie! 🔥",
    ),
    (
        "dramatic",
        lambda x, p, v:
        f"By the cosmic void, *{x}* radiates *{p}%* {v}! A LEGEND IS BORN! 🌌",
    ),
    ("meme",
     lambda x, p, v: f"*{x}* yeetin’ *{p}%* {v} like it’s 2012! Poggers! 😂"),
    (
        "epic",
        lambda x, p, v:
        f"ALERT: *{x}* is *{p}%* {v}! The multiverse quakes in awe! ⚡",
    ),
    (
        "clown",
        lambda x, p, v:
        f"Honka honka, *{x}* is *{p}%* {v}! Welcome to the circus, champ! 🤡",
    ),
    (
        "galactic",
        lambda x, p, v:
        f"*{x}* just warped to *{p}%* {v}! Aliens are taking notes! 👽",
    ),
    (
        "sarcastic",
        lambda x, p, v:
        f"Oh, wow, *{x}*, you’re a whopping *{p}%* {v}. Truly iconic. 🙄",
    ),
    (
        "pirate",
        lambda x, p, v:
        f"Argh, matey *{x}* be *{p}%* {v}! Sail the seas o’ chaos! 🏴‍☠️",
    ),
    (
        "doomer",
        lambda x, p, v:
        f"*{x}* is *{p}%* {v}, but, like, what’s the point anyway? 🖤",
    ),
    ("hype",
     lambda x, p, v: f"*{x}* is *{p}%* {v}! LET’S GOOOOOO, YOU LEGEND! 🚀"),
    (
        "cryptic",
        lambda x, p, v:
        f"*{x}* channels *{p}%* {v}. The ancient ones approve. 🕯️",
    ),
    (
        "retro",
        lambda x, p, v:
        f"*{x}* rockin’ *{p}%* {v}! Straight outta an 80s arcade! 🕹️",
    ),
    (
        "overly_enthusiastic",
        lambda x, p, v:
        f"OMG *{x}* IS *{p}%* {v}! YOU’RE LITERALLY THE GOAT! 🐐",
    ),
]

gay_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* gay! Serving rainbow realness like a pride float! 🌈",
    lambda x, p:
    f"*{x}* with *{p}%* gay vibes! You’re the glitter in the galaxy! 🏳️‍🌈",
    lambda x, p:
    f"Yo, *{x}* radiating *{p}%* gay energy! You’re a walking pride parade! 🎉",
    lambda x, p: f"*{x}* at *{p}%* gay! Slaying with that fabulous aura! ✨",
    lambda x, p:
    f"*{x}* dropping *{p}%* gay sparkles! You’re the king/queen of rainbows! 👑",
]

furry_flavors = [
    lambda x, p: f"*{x}* is *{p}%* furry! Tail wags and yiffs all around! 🐾",
    lambda x, p: f"*{x}* at *{p}%* furry vibes! Fursuit game too strong! 🦊",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* furry energy! You’re howling at the moon! 🐺",
    lambda x, p: f"*{x}* radiating *{p}%* furry chaos! Con badge ready! 😺",
    lambda x, p: f"*{x}* serving *{p}%* furry flair! Paws up, fam! 🐻",
]

vibe_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* vibin’! You’re the human equivalent of lo-fi beats! ☕",
    lambda x, p:
    f"*{x}* at *{p}%* vibe check! You’re chillin’ like a villain! 😎",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* vibe energy! You’re a walking aesthetic! ✨",
    lambda x, p:
    f"*{x}* radiating *{p}%* vibes! The universe is groovin’ with you! 🪐",
    lambda x, p: f"*{x}* dropping *{p}%* vibe bombs! Keep it 100! 🎶",
]

sus_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* sus! You ventin’ or just chillin’ in electrical? 🕵️‍♂️",
    lambda x, p:
    f"*{x}* at *{p}%* sus vibes! Crewmate or impostor? We’re watching! 👀",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* sus energy! Why you hiding in the vents? 🚨",
    lambda x, p:
    f"*{x}* radiating *{p}%* sus chaos! Emergency meeting incoming! 🚀",
    lambda x, p:
    f"*{x}* serving *{p}%* susness! You’re giving off impostor vibes! 😈",
]

roast_flavors = [
    lambda x, p:
    f"*{x}* just got *{p}%* roasted! Your drip’s so dry it’s a desert! 🔥",
    lambda x, p:
    f"Oof, *{x}* is *{p}%* toasted! Your vibes are stuck in a 90s dial-up! 💧",
    lambda x, p:
    f"*{x}*, *{p}%* burned! You’re so basic, you’re Comic Sans IRL! 😬",
    lambda x, p:
    f"*{x}* got *{p}%* roasted! Your fit’s giving clearance rack energy! 🛒",
    lambda x, p:
    f"*{x}* at *{p}%* roast level! You’re cooked like a microwave burrito! 🍳",
]

groupvibe_flavors = [
    lambda x, p:
    f"This group is *{p}%* lit! It’s a straight-up rave in here! 🎉",
    lambda x, p: f"Y’all are *{p}%* chaotic! This chat’s a meme war zone! 🤡",
    lambda x, p: f"Group vibe at *{p}%*! You’re the Avengers of nonsense! 💪",
    lambda x, p: f"This squad’s *{p}%* wild! Y’all breaking the internet! 🌋",
    lambda x, p:
    f"Group energy at *{p}%*! You’re the chaos crew of legends! 🚀",
]

vape_flavors = [
    lambda x, p: f"*{x}* is puffin’ *{p}%* clouds! Vape nation represent! 💨",
    lambda x, p:
    f"*{x}* just dropped a *{p}%* vape cloud so thicc it blocked the sun! 😶‍🌫️",
    lambda x, p:
    f"Yo, *{x}* is *{p}%* vapin’ like a dragon with a sick mod! 🔥",
    lambda x, p:
    f"*{x}* hittin’ *{p}%* vape juice so hard, the room’s a fog machine! 🌫️",
    lambda x, p:
    f"*{x}* with *{p}%* vape energy! You’re blowing rings to Jupiter! 🪐",
]

twink_flavors = [
    lambda x, p:
    f"*{x}* is sparkling at *{p}%* twink vibes! Pure fabulous energy! ✨",
    lambda x, p:
    f"*{x}* just hit *{p}%* twink status! The glitter gods approve! 💅",
    lambda x, p:
    f"OMG, *{x}* is *{p}%* twink-tastic! Slaying the aesthetic game! 🩷",
    lambda x, p:
    f"*{x}* radiating *{p}%* twink energy! The runway’s quaking! 🌟",
    lambda x, p:
    f"*{x}* serving *{p}%* twink realness! You’re a walking glow-up! 💖",
]

lesbian_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* sapphic superstar! Flannel and vibes on point! 🪵",
    lambda x, p:
    f"*{x}* rocking *{p}%* lesbian energy! Scissoring stereotypes like a pro! ✂️",
    lambda x, p:
    f"Yo, *{x}* is *{p}%* lesbian legend! U-Haul’s already parked! 🚚",
    lambda x, p:
    f"*{x}* serving *{p}%* queer queen vibes! The plaid gods salute you! 🌈",
    lambda x, p:
    f"*{x}* at *{p}%* lesbian power! You’re chopping wood and hearts! 🪓",
]

top_flavors = [
    lambda x, p: f"*{x}* is *{p}%* top! Calling all the shots like a boss! 👑",
    lambda x, p: f"*{x}* at *{p}%* top energy! You’re running this show! 💪",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* top vibes! You’re the CEO of dominance! 🔝",
    lambda x, p:
    f"*{x}* radiating *{p}%* top power! Everyone’s taking notes! 📋",
    lambda x, p:
    f"*{x}* serving *{p}%* top-tier energy! You’re the king of the castle! 🏰",
]

bottom_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* bottom! Cozy vibes and pillow forts galore! 🛌",
    lambda x, p:
    f"*{x}* at *{p}%* bottom energy! You’re the queen of chill! 😘",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* bottom vibes! You’re living the snuggle life! 💖",
    lambda x, p:
    f"*{x}* radiating *{p}%* bottom energy! Blanket throne ready! 🛏️",
    lambda x, p:
    f"*{x}* serving *{p}%* bottom realness! You’re the comfiest legend! 🧸",
]

rizz_flavors = [
    lambda x, p:
    f"*{x}* got *{p}%* rizz! Smooth talkin’ like a TikTok heartthrob! 😘",
    lambda x, p:
    f"*{x}* drippin’ *{p}%* rizzler energy! Rizz god status unlocked! 😎",
    lambda x, p:
    f"Wow, *{x}* with *{p}%* rizz! You’re stealing hearts like a pro thief! 💖",
    lambda x, p:
    f"*{x}* got that *{p}%* Ohio-level rizz! Skibidi toilet who? 🚽",
    lambda x, p:
    f"*{x}* serving *{p}%* rizz vibes! You’re charming the socks off everyone! 🧦",
]

sigma_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* sigma! Lone wolf grindset, no Ohio vibes! 🐺",
    lambda x, p:
    f"*{x}* radiating *{p}%* sigma energy! Betas can’t handle this! 💪",
    lambda x, p:
    f"*{x}* at *{p}%* sigma status! Out here rejecting the matrix! 🕶️",
    lambda x, p: f"*{x}* with *{p}%* sigma grind! You’re the CEO of based! 🏆",
    lambda x, p:
    f"*{x}* serving *{p}%* sigma vibes! You’re rewriting the rules! 📜",
]

simp_flavors = [
    lambda x, p: f"*{x}* is *{p}%* simp! Heart-eyes for days, my dude! 😍",
    lambda x, p:
    f"*{x}* at *{p}%* simp mode! Sending 10/10 e-girl donations! 💸",
    lambda x, p:
    f"*{x}* simpin’ at *{p}%*! You’re one OnlyFans sub away from broke! 🥺",
    lambda x, p:
    f"*{x}* with *{p}%* simp energy! Throne’s already gift-wrapped! 🎁",
    lambda x, p:
    f"*{x}* serving *{p}%* simp vibes! You’re DMing sonnets already! ✍️",
]

based_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* based! Truth bombs droppin’ like it’s 4chan! 💊",
    lambda x, p:
    f"*{x}* at *{p}%* based mode! You’re red-pilling the whole chat! 🟥",
    lambda x, p:
    f"*{x}* serving *{p}%* based vibes! Cancel culture’s shaking! 😤",
    lambda x, p:
    f"*{x}* with *{p}%* based energy! You’re the king of unfiltered! 🗣️",
    lambda x, p:
    f"*{x}* radiating *{p}%* based power! Normies can’t comprehend! 🧠",
]

horny_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* horny! Chill, it’s not that kind of chat! 😳",
    lambda x, p:
    f"*{x}* at *{p}%* spicy mode! Someone get this simp some ice! 🧊",
    lambda x, p: f"*{x}* with *{p}%* horniness! DMs about to get WILD! 🔥",
    lambda x, p: f"*{x}* radiating *{p}%* thirsty vibes! Thirst trap alert! 🚨",
    lambda x, p:
    f"*{x}* serving *{p}%* spicy energy! You’re one DM from chaos! 💦",
]

lgbtq_flavors = [
    lambda x, p: f"*{x}* is *{p}%* LGBTQ icon! Slaying the rainbow game! 🌈",
    lambda x, p: f"*{x}* rocking *{p}%* queer energy! Pride parade MVP! 🏳️‍🌈",
    lambda x, p:
    f"*{x}* at *{p}%* LGBTQ legend! You’re the glitter in the galaxy! ✨",
    lambda x, p:
    f"*{x}* with *{p}%* rainbow vibes! Love is love, and you’re winning! 🩷",
    lambda x, p:
    f"*{x}* serving *{p}%* queer realness! You’re a pride supernova! 🌟",
]

hot_flavors = [
    lambda x, p: f"*{x}* is *{p}%* HOT! Sizzling like a summer BBQ! 🔥",
    lambda x, p: f"*{x}* at *{p}%* spicy! You’re too hot for this server! 🌶️",
    lambda x, p: f"*{x}* radiating *{p}%* hotness! The chat’s melting! 😍",
    lambda x, p:
    f"*{x}* with *{p}%* fire! You’re basically a walking thirst trap! 💦",
    lambda x, p:
    f"*{x}* serving *{p}%* hot vibes! You’re burning up the group chat! 🔥",
]

wet_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* wet! Dripping like a rainy day in Seattle! ☔",
    lambda x, p: f"*{x}* at *{p}%* soggy vibes! You’re a walking waterpark! 💦",
    lambda x, p:
    f"Yo, *{x}* is *{p}%* drenched! Did you fall in a pool or what? 🏊",
    lambda x, p: f"*{x}* radiating *{p}%* wet energy! You’re making waves! 🌊",
    lambda x, p:
    f"*{x}* serving *{p}%* wet vibes! You’re a human splash zone! 💧",
]

cringe_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* cringe! Your vibes are giving 2010 YouTube energy! 😬",
    lambda x, p:
    f"*{x}* at *{p}%* cringe factor! Did you just quote a TikTok from 2019? 🫣",
    lambda x, p:
    f"Oof, *{x}* with *{p}%* cringe! My secondhand embarrassment is through the roof! 🙈",
    lambda x, p:
    f"*{x}* serving *{p}%* cringe vibes! You’re a walking awkward moment! 😅",
    lambda x, p:
    f"*{x}* radiating *{p}%* cringe energy! You’re the king of facepalms! 🤦",
]

goofy_flavors = [
    lambda x, p: f"*{x}* is *{p}%* goofy! You’re out here acting unwise! 🤪",
    lambda x, p:
    f"*{x}* at *{p}%* goofy energy! Goofy Goober would be proud! 🦁",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* goofball vibes! You’re one step from a clown wig! 🤡",
    lambda x, p:
    f"*{x}* radiating *{p}%* goofy chaos! Keepin’ it silly since day one! 😜",
    lambda x, p:
    f"*{x}* serving *{p}%* goofy vibes! You’re a cartoon in human form! 📺",
]

npc_flavors = [
    lambda x, p: f"*{x}* is *{p}%* NPC! Just following the script, huh? 📜",
    lambda x, p:
    f"*{x}* at *{p}%* NPC vibes! You got a quest marker above your head! ❗",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* NPC energy! Repeating the same dialogue loop! 🔄",
    lambda x, p:
    f"*{x}* serving *{p}%* NPC status! Are you even a main character? 🤖",
    lambda x, p:
    f"*{x}* radiating *{p}%* NPC vibes! You’re stuck in the tutorial zone! 🎮",
]

uwu_flavors = [
    lambda x, p:
    f"*{x}*-chan is *{p}%* uwu! So kawaii, my heart can’t handle it! >w<",
    lambda x, p: f"*{x}* at *{p}%* uwu energy! Pwease, you’re too adorable! 🥺",
    lambda x, p:
    f"Nya, *{x}* with *{p}%* uwu vibes! You’re a walking anime convention! 😽",
    lambda x, p: f"*{x}* radiating *{p}%* uwu power! Senpai noticed you! 💖",
    lambda x, p:
    f"*{x}* serving *{p}%* uwu realness! You’re the cutest neko ever! 🐾",
]

emo_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* emo! My Chemical Romance wrote a song about you! 🖤",
    lambda x, p:
    f"*{x}* at *{p}%* emo vibes! Your eyeliner’s crying harder than you! 😢",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* emo energy! Dashboard Confessional’s got nothing on you! 🎸",
    lambda x, p:
    f"*{x}* serving *{p}%* emo angst! The darkness calls your name! 🌑",
    lambda x, p:
    f"*{x}* radiating *{p}%* emo vibes! You’re a walking sad playlist! 🎶",
]

clown_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* clown! Honk honk, you’re running the circus! 🤡",
    lambda x, p:
    f"*{x}* at *{p}%* clown energy! You’re one balloon away from a parade! 🎈",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* clown vibes! The big top’s calling your name! 🎪",
    lambda x, p:
    f"*{x}* radiating *{p}%* clown chaos! Pennywise wishes he had your drip! 🩸",
    lambda x, p:
    f"*{x}* serving *{p}%* clown realness! You’re the jester of chaos! 🃏",
]

gigachad_flavors = [
    lambda x, p:
    f"*{x}* is *{p}%* GIGACHAD! Jawline sharper than a diamond blade! 😎",
    lambda x, p:
    f"*{x}* at *{p}%* GIGACHAD energy! You bench press planets for fun! 💪",
    lambda x, p:
    f"Yo, *{x}* with *{p}%* GIGACHAD vibes! You’re the final boss of masculinity! 🏋️",
    lambda x, p:
    f"*{x}* radiating *{p}%* GIGACHAD power! The universe kneels before you! 🦁",
    lambda x, p:
    f"*{x}* serving *{p}%* GIGACHAD realness! You’re a walking legend meme! 🗿",
]

iq_flavors = [
    lambda x, p: f"*{x}* has *{p}* IQ! Brainpower off the charts! 🧠",
    lambda x, p:
    f"*{x}* with *{p}* IQ! You’re solving equations in your sleep! 📊",
    lambda x, p: f"Yo, *{x}* at *{p}* IQ! Einstein’s taking notes! 🤓",
    lambda x, p:
    f"*{x}* radiating *{p}* IQ! You’re a walking supercomputer! 💻",
    lambda x, p:
    f"*{x}* serving *{p}* IQ vibes! You’re outsmarting the multiverse! 🌌",
]

emojis = {
    "gay": ["🌈", "🏳️‍🌈", "🎉"],
    "furry": ["🐾", "😺", "🦊"],
    "vibe": ["✨", "☕", "😎"],
    "sus": ["🕵️‍♂️", "🚀", "👀"],
    "roast": ["🔥", "💧", "😬"],
    "groupvibe": ["🎉", "🤡", "💪"],
    "vape": ["💨", "😶‍🌫️", "🔋"],
    "twink": ["✨", "💅", "🩷"],
    "lesbian": ["🌈", "🪵", "✂️"],
    "top": ["👑", "💪", "🔝"],
    "bottom": ["😘", "🛌", "💖"],
    "rizz": ["😎", "💖", "😘"],
    "sigma": ["🐺", "🕶️", "💪"],
    "simp": ["😍", "🥺", "💸"],
    "based": ["💊", "🟥", "😤"],
    "horny": ["😳", "🔥", "🧊"],
    "lgbtq": ["🌈", "🏳️‍🌈", "🩷"],
    "hot": ["🔥", "🌶️", "😍"],
    "wet": ["💦", "☔", "🌊"],
    "cringe": ["😬", "🫣", "🙈"],
    "goofy": ["🤪", "😜", "🤡"],
    "npc": ["🤖", "📜", "❗"],
    "uwu": ["🥺", "😽", "💖"],
    "emo": ["🖤", "😢", "🎸"],
    "clown": ["🤡", "🎈", "🎪"],
    "gigachad": ["😎", "💪", "🦁"],
    "iq": ["🧠", "📊", "🤓"],
}

cooldowns = defaultdict(lambda: defaultdict(float))
COOLDOWN_TIME = 10


def dice(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "dice", update, skip_if_privileged=True):
        return
    update.message.reply_dice(emoji=Dice.DICE)


def dart(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "dart", update, skip_if_privileged=True):
        return
    update.message.reply_dice(emoji=Dice.DARTS)


def basket(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "basket", update, skip_if_privileged=True):
        return
    update.message.reply_dice(emoji=Dice.BASKETBALL)


def football(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "football", update, skip_if_privileged=True):
        return
    update.message.reply_dice(emoji=Dice.FOOTBALL)


def slotmachine(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "slotmachine", update, skip_if_privileged=True):
        return
    update.message.reply_dice(emoji=Dice.SLOT_MACHINE)


def bowling(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "bowling", update, skip_if_privileged=True):
        return
    update.message.reply_dice(emoji=Dice.BOWLING)


def alldice(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "alldice", update, skip_if_privileged=True):
        return
    update.message.reply_dice(emoji=Dice.DICE)
    update.message.reply_dice(emoji=Dice.DARTS)
    update.message.reply_dice(emoji=Dice.BASKETBALL)
    update.message.reply_dice(emoji=Dice.FOOTBALL)
    update.message.reply_dice(emoji=Dice.SLOT_MACHINE)
    update.message.reply_dice(emoji=Dice.BOWLING)


def check_cooldown(user_id: int, command: str, update: Update, skip_if_privileged: bool = False) -> bool:
    if skip_if_privileged and is_privileged_user(user_id):
        return True

    current_time = time.time()
    last_used = cooldowns[user_id][command]
    if current_time - last_used < COOLDOWN_TIME:
        remaining = int(COOLDOWN_TIME - (current_time - last_used))
        update.message.reply_text(
            f"Chill, {update.effective_user.first_name}! Wait {remaining}s before using /{command} again! ⏳"
        )
        return False

    cooldowns[user_id][command] = current_time
    return True


def get_random_flavor(name: str, percentage: int, value: str) -> str:
    flavor, func = random.choice(response_flavors)
    return func(name, percentage, value)


def get_random_emoji(command: str) -> str:
    return random.choice(emojis[command])


def extract_target(update: Update, default_name: str) -> str:
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user.first_name
    return default_name


def gay(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "gay", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so gay you’re leading the pride parade! 🌈🏳️‍🌈",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(gay_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "gay"))
    update.message.reply_text(f"{reply} {get_random_emoji('gay')}",
                              parse_mode="Markdown")
    if percentage > 90:
        update.message.reply_text(
            "Rainbow overload! You're the glitter king/queen of pride! 🏳️‍🌈")
    elif percentage < 30:
        update.message.reply_text(
            "Low rainbow vibes? Grab some sparkles and try again! ✨")


def furry(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "furry", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so furry you’re headlining the next con! 🐾🎉",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(furry_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "furry"))
    update.message.reply_text(f"{reply} {get_random_emoji('furry')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Yiff levels critical! Time to unleash your inner fox! 🦊")
    elif percentage < 20:
        update.message.reply_text(
            "No tail wag? Maybe you’re just a human in denial! 😿")


def vibe(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "vibe", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! Your vibes are so high you’re floating in space! ✨🪐",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(vibe_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "vibin'"))
    update.message.reply_text(f"{reply} {get_random_emoji('vibe')}",
                              parse_mode="Markdown")
    if percentage > 85:
        update.message.reply_text(
            "Your vibes are so high, you’re orbiting Saturn! 🪐")
    elif percentage < 25:
        update.message.reply_text(
            "Vibe check failed! Chug an energy drink, stat! ⚡")


def sus(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "sus", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so sus you’re banned from Among Us! 🚨👀",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(sus_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "sus"))
    update.message.reply_text(f"{reply} {get_random_emoji('sus')}",
                              parse_mode="Markdown")
    if percentage > 75:
        update.message.reply_text(
            "Emergency meeting! You’re ventin’ too hard! 🚨")
    elif percentage < 30:
        update.message.reply_text(
            "Crewmate confirmed? Nah, you’re still a bit shady! 😆")


def roast(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "roast", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so roasted you’re a burnt marshmallow! 🔥😬",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(roast_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "roasted"))
    update.message.reply_text(f"{reply} {get_random_emoji('roast')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Burn unit on standby! That roast was LETHAL! 🚑")


def group_vibe(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "groupvibe", update, skip_if_privileged=True):
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(groupvibe_flavors)(None, percentage)
             if random.random() < 0.5 else get_random_flavor(
                 "This group", percentage, "vibin'"))
    update.message.reply_text(f"{reply} {get_random_emoji('groupvibe')}",
                              parse_mode="Markdown")
    if percentage > 95:
        update.message.reply_text(
            "This chat’s energy is breaking the internet! Keep it 1000! 🌋")
    elif percentage < 40:
        update.message.reply_text(
            "Group vibe’s kinda dead... someone drop a meme! 📉")


def vape(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "vape", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"Oh no, *{name}*! Your vape mod short-circuited! Sparks everywhere! ⚡💥",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(vape_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "vapin'"))
    update.message.reply_text(f"{reply} {get_random_emoji('vape')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Cloud chaser supreme! You’re blowing vape rings to the MOON! 🌕")
    elif percentage < 30:
        update.message.reply_text(
            "Weak clouds, bro! Upgrade that coil and hit harder! 🔧")


def twink(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "twink", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"OMG, *{name}*! You’re so twink you drowned in glitter! Save some sparkle for the rest of us! ✨💥",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(twink_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "twink"))
    update.message.reply_text(f"{reply} {get_random_emoji('twink')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Glitter god status! You’re serving looks that SLAY! 💃")
    elif percentage < 30:
        update.message.reply_text(
            "Not twink enough? Time to crank up the fabulous! 🩷")


def lesbian(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "lesbian", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so lesbian you’ve got a U-Haul on speed dial! 🚚💨",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(lesbian_flavors)(name, percentage)
             if random.random() < 0.5 else get_random_flavor(
                 name, percentage, "lesbian"))
    update.message.reply_text(f"{reply} {get_random_emoji('lesbian')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Sapphic queen alert! You’re rewriting the lesbian manifesto! 📜")
    elif percentage < 30:
        update.message.reply_text(
            "Low flannel vibes? Time to chop some wood and try again! 🪓")


def top(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "top", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so top you’re calling ALL the shots! Bow down! 👑",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(top_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "top"))
    update.message.reply_text(f"{reply} {get_random_emoji('top')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Ultimate top energy! You’re running this show like a boss! 💪")
    elif percentage < 30:
        update.message.reply_text(
            "Top vibes fading? Maybe lean into that power move! 😤")


def bottom(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "bottom", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so bottom you’ve got a pillow throne ready! 🛌😘",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(bottom_flavors)(name, percentage)
             if random.random() < 0.5 else get_random_flavor(
                 name, percentage, "bottom"))
    update.message.reply_text(f"{reply} {get_random_emoji('bottom')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Bottom royalty! You’re living your best cozy life! 🛏️")
    elif percentage < 30:
        update.message.reply_text(
            "Low bottom energy? Time to embrace the chill vibes! 😴")


def rizz(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "rizz", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! Your rizz is so strong you’re banned from Ohio! Skibidi who? 🚽💥",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(rizz_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "rizz"))
    update.message.reply_text(f"{reply} {get_random_emoji('rizz')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Rizzler supreme! You’re pulling hearts left and right! 😘")
    elif percentage < 30:
        update.message.reply_text(
            "Rizz running low? Time to crank up the charm! 😎")


def sigma(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "sigma", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so sigma you’re ghosting the entire alpha-beta system! 🐺🚪",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(sigma_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "sigma"))
    update.message.reply_text(f"{reply} {get_random_emoji('sigma')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Sigma grindset maxed! You’re out here rewriting the rules! 🕶️")
    elif percentage < 30:
        update.message.reply_text(
            "Sigma vibes low? Time to lone-wolf it up! 🐺")


def simp(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "simp", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re simping so hard your wallet’s crying! 💸😭",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(simp_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "simp"))
    update.message.reply_text(f"{reply} {get_random_emoji('simp')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Simp king/queen! You’re one donation away from a shrine! 🥺")
    elif percentage < 30:
        update.message.reply_text(
            "Low simp energy? Maybe you’re just playing hard to get! 😏")


def based(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "based", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so based you’re banned from every normie server! 💊🚫",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(based_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "based"))
    update.message.reply_text(f"{reply} {get_random_emoji('based')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Based god status! You’re dropping truth bombs like a pro! 🗣️")
    elif percentage < 30:
        update.message.reply_text(
            "Low based vibes? Time to crank up the red pills! 🟥")


def horny(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "horny", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so horny you’re setting off thirst alarms! 🚨😳",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(horny_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "horny"))
    update.message.reply_text(f"{reply} {get_random_emoji('horny')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Thirst levels critical! Someone get this user a cold shower! 🧊")
    elif percentage < 30:
        update.message.reply_text(
            "Low spicy vibes? Time to turn up the heat! 🔥")


def lgbtq(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "lgbtq", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so LGBTQ you’re leading the next pride parade! 🌈🏳️‍🌈",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(lgbtq_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "LGBTQ"))
    update.message.reply_text(f"{reply} {get_random_emoji('lgbtq')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Rainbow legend! You’re the heart of the pride party! 🩷")
    elif percentage < 30:
        update.message.reply_text(
            "Low queer vibes? Grab a flag and join the parade! 🌈")


def hot(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "hot", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so hot you’re causing a global heatwave! 🔥🌍",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(hot_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "hot"))
    update.message.reply_text(f"{reply} {get_random_emoji('hot')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Scorching hot! You’re burning up the chat! 🌶️")
    elif percentage < 30:
        update.message.reply_text("Low heat? Time to turn up the sizzle! 😎")


def wet(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "wet", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so wet you’re causing a tsunami! 🌊🚨",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(wet_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "wet"))
    update.message.reply_text(f"{reply} {get_random_emoji('wet')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Dripping legend! You’re practically a walking ocean! 🌊")
    elif percentage < 30:
        update.message.reply_text("Low wet vibes? Time to dive into a pool! 🏊")


def cringe(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "cringe", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so cringe you’re giving everyone secondhand embarrassment! 😬🚨",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(cringe_flavors)(name, percentage)
             if random.random() < 0.5 else get_random_flavor(
                 name, percentage, "cringe"))
    update.message.reply_text(f"{reply} {get_random_emoji('cringe')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Cringe king/queen! You’re the CEO of awkward moments! 🙈")
    elif percentage < 30:
        update.message.reply_text(
            "Low cringe vibes? Maybe you’re just too smooth! 😎")


def goofy(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "goofy", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so goofy you’re starring in a cartoon! 🤪🎬",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(goofy_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "goofy"))
    update.message.reply_text(f"{reply} {get_random_emoji('goofy')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Goofy god status! You’re the king/queen of silly! 😜")
    elif percentage < 30:
        update.message.reply_text(
            "Low goofy vibes? Time to crank up the silliness! 🤡")


def npc(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "npc", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so NPC you’re stuck in a dialogue loop! 📜🔄",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(npc_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "NPC"))
    update.message.reply_text(f"{reply} {get_random_emoji('npc')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Ultimate NPC! You’re out here living the side quest life! 🤖")
    elif percentage < 30:
        update.message.reply_text(
            "Low NPC vibes? Time to become the main character! 🌟")


def uwu(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "uwu", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*-chan! You’re so uwu you’re melting senpai’s heart! >w< 💖",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(uwu_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "uwu"))
    update.message.reply_text(f"{reply} {get_random_emoji('uwu')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Kawaii overload! You’re the ultimate uwu icon! 😽")
    elif percentage < 30:
        update.message.reply_text(
            "Low uwu vibes? Time to crank up the kawaii! 🥺")


def emo(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "emo", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so emo you’re writing poetry in the dark! 🖤✍️",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(emo_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "emo"))
    update.message.reply_text(f"{reply} {get_random_emoji('emo')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Emo legend! You’re the king/queen of angsty anthems! 🎸")
    elif percentage < 30:
        update.message.reply_text("Low emo vibes? Time to crank up the MCR! 🖤")


def clown(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "clown", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so clown you’re headlining the circus! 🤡🎪",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(clown_flavors)(name, percentage) if random.random()
             < 0.5 else get_random_flavor(name, percentage, "clown"))
    update.message.reply_text(f"{reply} {get_random_emoji('clown')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "Clown royalty! You’re running the big top like a boss! 🎈")
    elif percentage < 30:
        update.message.reply_text("Low clown vibes? Time to honk it up! 🤡")


def gigachad(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "gigachad", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! You’re so GIGACHAD you’re flexing on the entire multiverse! 💪🌌",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(0, 100)
    reply = (random.choice(gigachad_flavors)(name, percentage)
             if random.random() < 0.5 else get_random_flavor(
                 name, percentage, "GIGACHAD"))
    update.message.reply_text(f"{reply} {get_random_emoji('gigachad')}",
                              parse_mode="Markdown")
    if percentage > 80:
        update.message.reply_text(
            "GIGACHAD supreme! You’re the ultimate legend of legends! 🦁")
    elif percentage < 30:
        update.message.reply_text(
            "Low GIGACHAD vibes? Time to crank up the testosterone! 😎")


def iq(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if not check_cooldown(user.id, "iq", update, skip_if_privileged=True):
        return
    name = extract_target(update, user.first_name)
    if random.random() < 0.05:
        update.message.reply_text(
            f"*{name}*! Your IQ is so high you’re solving quantum physics in your sleep! 🧠💥",
            parse_mode="Markdown",
        )
        return
    percentage = random.randint(50, 150)
    reply = random.choice(iq_flavors)(name, percentage)
    update.message.reply_text(f"{reply} {get_random_emoji('iq')}",
                              parse_mode="Markdown")
    if percentage > 130:
        update.message.reply_text(
            "Genius alert! You’re out here inventing new dimensions! 📊")
    elif percentage < 80:
        update.message.reply_text(
            "Low IQ vibes? Maybe stick to memes for now! 🤓")


__help__ = """
*Fun Commands:*
 - /gay: Checks how gay you or a replied-to user are. Rainbow vibes incoming! 🌈
 - /furry: Measures your or a replied-to user's furry energy. Paws up! 🐾
 - /vibe: Runs a vibe check on you or a replied-to user. Are you chillin'? 😎
 - /sus: Determines how sus you or a replied-to user are. Vent check! 👀
 - /roast: Roasts you or a replied-to user with some spicy burns! 🔥
 - /groupvibe: Checks the whole group's vibe. Is this chat lit or dead? 🎉
 - /vape: Measures your or a replied-to user's vape cloud skills. Puff puff! 💨
 - /twink: Rates your or a replied-to user's twink fabulousness. Glitter alert! ✨
 - /lesbian: Checks your or a replied-to user's sapphic energy. Flannel power! 🪵
 - /top: Determines how top-tier you or a replied-to user are. Boss mode! 👑
 - /bottom: Rates your or a replied-to user's cozy bottom vibes. Pillow forts! 🛌
 - /rizz: Measures your or a replied-to user's rizzler charm. Smooth or Ohio? 😘
 - /sigma: Checks your or a replied-to user's lone wolf sigma grind. 🐺
 - /simp: Rates your or a replied-to user's simp dedication. Heart-eyes much? 😍
 - /based: Determines how based you or a replied-to user are. Truth bombs! 💊
 - /horny: Checks your or a replied-to user's thirst levels. Chill, fam! 😳
 - /lgbtq: Rates your or a replied-to user's rainbow icon status. Pride vibes! 🏳️‍🌈
 - /hot: Measures how hot you or a replied-to user are. Sizzling or not? 🔥
 - /wet: Checks your or a replied-to user's drippy energy. Tsunami alert! 💦
 - /cringe: Rates your or a replied-to user's cringe factor. Secondhand embarrassment! 😬
 - /goofy: Measures your or a replied-to user's goofball energy. Silly mode! 🤪
 - /npc: Checks how NPC you or a replied-to user are. Main character or side quest? 🤖
 - /uwu: Rates your or a replied-to user's kawaii uwu vibes. Senpai approved! 🥺
 - /emo: Measures your or a replied-to user's angsty emo energy. Eyeliner tears! 🖤
 - /clown: Rates your or a replied-to user's circus-ready clown vibes. Honk honk! 🤡
 - /gigachad: Checks your or a replied-to user's GIGACHAD status. Ultimate legend! 💪
 - /iq: Measures your or a replied-to user's brainpower. Genius or meme lord? 🧠

*Emoji Dice Commands:*
 - /basket: Shoot a basketball. Will it land? 🏀
 - /bowling: Try to bowl a strike! 🎳
 - /dart: Hit the bullseye with a dart! 🎯
 - /dice: Classic 6-sided dice roll! 🎲
 - /football: Try to score a goal! ⚽
 - /slotmachine: Spin the slots and test your luck! 🎰
 - /alldice: Show off all supported dice types at once!

*Note*: Reply to a message to target another user, or the bot will rate you! All commands have a 10-second cooldown to keep the chaos in check. 😜
"""

__mod_name__ = "Fun"

dispatcher.add_handler(CommandHandler("basket", basket, run_async=True))
dispatcher.add_handler(CommandHandler("bowling", bowling, run_async=True))
dispatcher.add_handler(CommandHandler("dart", dart, run_async=True))
dispatcher.add_handler(CommandHandler("dice", dice, run_async=True))
dispatcher.add_handler(CommandHandler("football", football, run_async=True))
dispatcher.add_handler(CommandHandler("slotmachine", slotmachine, run_async=True))
dispatcher.add_handler(CommandHandler("alldice", alldice, run_async=True))
dispatcher.add_handler(CommandHandler("gay", gay, run_async=True))
dispatcher.add_handler(CommandHandler("furry", furry, run_async=True))
dispatcher.add_handler(CommandHandler("vibe", vibe, run_async=True))
dispatcher.add_handler(CommandHandler("sus", sus, run_async=True))
dispatcher.add_handler(CommandHandler("roast", roast, run_async=True))
dispatcher.add_handler(CommandHandler("groupvibe", group_vibe, run_async=True))
dispatcher.add_handler(CommandHandler("vape", vape, run_async=True))
dispatcher.add_handler(CommandHandler("twink", twink, run_async=True))
dispatcher.add_handler(CommandHandler("lesbian", lesbian, run_async=True))
dispatcher.add_handler(CommandHandler("top", top, run_async=True))
dispatcher.add_handler(CommandHandler("bottom", bottom, run_async=True))
dispatcher.add_handler(CommandHandler("rizz", rizz, run_async=True))
dispatcher.add_handler(CommandHandler("sigma", sigma, run_async=True))
dispatcher.add_handler(CommandHandler("simp", simp, run_async=True))
dispatcher.add_handler(CommandHandler("based", based, run_async=True))
dispatcher.add_handler(CommandHandler("horny", horny, run_async=True))
dispatcher.add_handler(CommandHandler("lgbtq", lgbtq, run_async=True))
dispatcher.add_handler(CommandHandler("hot", hot, run_async=True))
dispatcher.add_handler(CommandHandler("wet", wet, run_async=True))
dispatcher.add_handler(CommandHandler("cringe", cringe, run_async=True))
dispatcher.add_handler(CommandHandler("goofy", goofy, run_async=True))
dispatcher.add_handler(CommandHandler("npc", npc, run_async=True))
dispatcher.add_handler(CommandHandler("uwu", uwu, run_async=True))
dispatcher.add_handler(CommandHandler("emo", emo, run_async=True))
dispatcher.add_handler(CommandHandler("clown", clown, run_async=True))
dispatcher.add_handler(CommandHandler("gigachad", gigachad, run_async=True))
dispatcher.add_handler(CommandHandler("iq", iq, run_async=True))
