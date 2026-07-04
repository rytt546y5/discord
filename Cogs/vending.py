import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os
import uuid
import io
from utils import is_allowed
import paypayu
import random

VENDING_DATA_FILE = "vending_data.json"
PAYPAY_DATA_FILE = "paypay_data.json"
STOCK_DIR_BASE = "stock_files"
STOCK_NOTIFICATION_DATA_FILE = "stock_notification_data.json"
COUPON_DATA_FILE = "coupon_data.json"
ROLE_ASSIGNMENT_DATA_FILE = "role_assignment_data.json"

os.makedirs(STOCK_DIR_BASE, exist_ok=True)

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:

            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_paypay_data():
    if os.path.exists(PAYPAY_DATA_FILE):
        with open(PAYPAY_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_stock_notification_data():
    if os.path.exists(STOCK_NOTIFICATION_DATA_FILE):
        with open(STOCK_NOTIFICATION_DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_stock_notification_data(data):
    with open(STOCK_NOTIFICATION_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_coupon_data():
    if os.path.exists(COUPON_DATA_FILE):
        with open(COUPON_DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_coupon_data(data):
    with open(COUPON_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_role_assignment_data():
    if os.path.exists(ROLE_ASSIGNMENT_DATA_FILE):
        with open(ROLE_ASSIGNMENT_DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_role_assignment_data(data):
    with open(ROLE_ASSIGNMENT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

async def vending_machine_autocomplete(interaction: discord.Interaction, current: str):
    vending_data = load_json(VENDING_DATA_FILE)
    user_id_str = str(interaction.user.id)

    user_machines = []

    for vm_id, vm_data in vending_data.items():
        if not isinstance(vm_data, dict):
            continue

        if vm_data.get("owner_id") == user_id_str:
            user_machines.append((vm_id, vm_data))

    return [
        app_commands.Choice(
            name=vm_data.get("name", "åç§°æªè¨­å®"),
            value=vm_id
        )
        for vm_id, vm_data in user_machines
        if current.lower() in vm_data.get("name", "").lower()
    ]

async def coupon_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    coupon_data = load_coupon_data()
    user_id_str = str(interaction.user.id)
    
    user_coupons = [
        (coupon_code, coupon_info) for coupon_code, coupon_info in coupon_data.items()
        if coupon_info.get("owner_id") == user_id_str
    ]
    
    choices = []
    for coupon_code, coupon_info in user_coupons:
        if current.lower() in coupon_code.lower():
            discount = coupon_info.get("discount", 0)
            vending_machine_id = coupon_info.get("vending_machine_id", "")
            vending_data = load_json(VENDING_DATA_FILE)
            vm_name = vending_data.get(vending_machine_id, {}).get("name", "ä¸æ")
            choices.append(app_commands.Choice(
                name=f"{coupon_code} (-{discount}å) [{vm_name}]",
                value=coupon_code
            ))
    
    return choices[:25]

async def role_assignment_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    role_data = load_role_assignment_data()
    vending_data = load_json(VENDING_DATA_FILE)
    
    choices = []
    for vm_id, role_info in role_data.items():
        if role_info.get("guild_id") == interaction.guild.id:
            vm = vending_data.get(vm_id)
            if vm and vm.get("owner_id") == str(interaction.user.id):
                vm_name = vm.get("name", "ä¸æãªèªè²©æ©")
                if current.lower() in vm_name.lower():
                    choices.append(app_commands.Choice(name=vm_name, value=vm_id))
    
    return choices[:25]

async def handle_error(interaction: discord.Interaction, error: Exception, ephemeral: bool = True):
    """çµ±ä¸ã¨ã©ã¼ãã³ããªã³ã°"""
    try:
        embed = discord.Embed(
            title="ã¨ã©ã¼ãçºçãã¾ãã",
            description=f"```{str(error)}```",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=interaction.client.embed_footer)
        
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
    except:
        print(f"Error sending error message: {error}")

async def check_stock(interaction: discord.Interaction, products: list):
    embed = discord.Embed(
        title="å¨åº«ã»è²©å£²æ°æå ±",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=interaction.client.embed_footer)

    if not products:
        embed.description = "ãã®èªè²©æ©ã«ã¯ååãç»é²ããã¦ãã¾ããã"
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    for product in products:
        product_name = product.get("name", "ä¸æ")
        sales_count = product.get("sales_count", 0)
        
        if product.get("infinite_stock"):
            # ç¡éå¨åº«ã®å ´å
            embed.add_field(
                name=f"{product_name}", 
                value=f"```å¨åº«æ°: âå\nè²©å£²æ°: {sales_count}å```", 
                inline=False
            )
        else:
            # æéå¨åº«ã®å ´å
            stock_file = product.get("stock_file")
            
            if not stock_file:
                embed.add_field(
                    name=f"{product_name}", 
                    value=f"```å¨åº«æ°: ä¸æ\nè²©å£²æ°: {sales_count}å```", 
                    inline=False
                )
                continue
                
            try:
                with open(stock_file, "r", encoding="utf-8") as file:
                    lines = [line for line in file.readlines() if line.strip()]
                    stock_count = len(lines)
                    embed.add_field(
                        name=f"{product_name}", 
                        value=f"```å¨åº«æ°: {stock_count}å\nè²©å£²æ°: {sales_count}å```", 
                        inline=False
                    )

            except FileNotFoundError:
                embed.add_field(
                    name=f"{product_name}", 
                    value=f"```å¨åº«æ°: 0å\nè²©å£²æ°: {sales_count}å```", 
                    inline=False
                )
            except Exception as e:
                await handle_error(interaction, e)

    await interaction.followup.send(embed=embed, ephemeral=True)


class VendingMachineCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Cogã­ã¼ãæã«æ°¸ç¶åViewãå¾©å"""
        vending_data = load_json(VENDING_DATA_FILE)
        
        # èªè²©æ©ããã«ç¨Viewãå¾©å
        for vm_id in vending_data.keys():
            view = VendingMachineCog.VendingMachineView(vm_id, self.bot)
            self.bot.add_view(view)
        
        # ãã®ä»ã®æ°¸ç¶åViewãå¾©å
        products_data = []
        for vm_id, vm_data in vending_data.items():
            if not isinstance(vm_data, dict):
                continue

            products = vm_data.get("products", [])
            if isinstance(products, list):
                products_data.extend(products)

        
        if products_data:
            # å¨åº«è¿½å ç¨View
            stock_view = VendingMachineCog.ProductSelectViewForStock(products_data)
            self.bot.add_view(stock_view)
            
            # å¨åº«å¼åºç¨View
            withdraw_view = VendingMachineCog.WithdrawStockView(products_data, 1)
            self.bot.add_view(withdraw_view)
            
            # å¨åº«åå®¹ç¢ºèªç¨View
            content_view = VendingMachineCog.ContentView(products_data)
            self.bot.add_view(content_view)

    @staticmethod
    async def refresh_panel(bot, vending_machine_id):
        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm:
            return

        channel = bot.get_channel(vm.get("panel_channel_id"))
        if not channel:
            return

        try:
            msg = await channel.fetch_message(vm.get("panel_message_id"))
        except:
            return

        embed = discord.Embed(
            title="èªè²©æ©",
            description="ååãé¸æãã¦ãã ããã",
            color=discord.Color.green()
        )

        view = VendingMachineCog.VendingMachineView(vending_machine_id, bot)
        await msg.edit(embed=embed, view=view)

    @app_commands.command(name="èªè²©æ©ä½æ", description="èªè²©æ©ãä½æãã¾ã")
    @is_allowed()
    @app_commands.describe(name="èªè²©æ©ã®åå")
    async def vm_create(self, interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        vending_data = load_json(VENDING_DATA_FILE)
        new_vm_id = str(uuid.uuid4())

        # PayPayã¢ã«ã¦ã³ããç»é²ããã¦ããããã§ãã¯
        paypay_data = load_paypay_data()
        paypay_id = user_id if user_id in paypay_data else None

        vending_data[new_vm_id] = {
            "name": name,
            "owner_id": user_id,
            "paypay_id": paypay_id,
            "log_channel_id": None,
            "private_log_channel_id": None,
            "panel_message_id": None,
            "panel_channel_id": None,
            "products": []
        }
        save_json(VENDING_DATA_FILE, vending_data)

        if paypay_id:
            await interaction.response.send_message(f"èªè²©æ©ã{name}ããä½æãã¾ããã\n**èªè²©æ©ID:** `{new_vm_id}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"èªè²©æ©ã{name}ããä½æãã¾ããã\n**èªè²©æ©ID:** `{new_vm_id}`\nPayPayã¢ã«ã¦ã³ããæªç»é²ã§ãã`/paypayç»é²` ãå®è¡ãã¦ãã ããã", ephemeral=True)

    @app_commands.command(name="å¬éã­ã°è¨­å®", description="å¬éè²©å£²ã­ã°ãéä¿¡ãããã£ã³ãã«ãè¨­å®ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="èªè²©æ©", channel="ã­ã°ãéä¿¡ãããã£ã³ãã«")
    async def vm_set_log(self, interaction: discord.Interaction, vending_machine_id: str, channel: discord.TextChannel):
        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm or vm.get("owner_id") != str(interaction.user.id):
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
        
        vm["log_channel_id"] = channel.id
        save_json(VENDING_DATA_FILE, vending_data)
        await interaction.response.send_message(f"èªè²©æ©ã{vm['name']}ãã®ã­ã°ãã£ã³ãã«ã {channel.mention} ã«è¨­å®ãã¾ããã", ephemeral=True)

    @app_commands.command(name="éå¬éã­ã°è¨­å®", description="éå¬éè²©å£²ã­ã°ãéä¿¡ãããã£ã³ãã«ãè¨­å®ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="èªè²©æ©", channel="ã­ã°ãéä¿¡ãããã£ã³ãã«")
    async def vm_set_private_log(self, interaction: discord.Interaction, vending_machine_id: str, channel: discord.TextChannel):
        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm or vm.get("owner_id") != str(interaction.user.id):
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
        
        vm["private_log_channel_id"] = channel.id
        save_json(VENDING_DATA_FILE, vending_data)
        
        await interaction.response.send_message(f"èªè²©æ©ã{vm['name']}ãã®éå¬éã­ã°ãã£ã³ãã«ã {channel.mention} ã«è¨­å®ãã¾ããã", ephemeral=True)

    @app_commands.command(name="ååè¿½å ", description="æå®ããèªè²©æ©ã«æ°ããååãè¿½å ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="ååãç»é²ããèªè²©æ©",name="ååå",description="ååèª¬æï¼ä»»æï¼",price="ä¾¡æ ¼",emoji="ååçµµæå­")
    async def vm_add_product(self, interaction: discord.Interaction, vending_machine_id: str, name: str, price: int, description: str = None, emoji: str=None):
        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm or vm.get("owner_id") != str(interaction.user.id):
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)

        product_id = str(uuid.uuid4())
        stock_file_path = os.path.join(STOCK_DIR_BASE, f"{product_id}.txt")
        with open(stock_file_path, "w", encoding="utf-8") as f:
            pass

        new_product = {
            "product_id": product_id,
            "name": name,
            "description": description or "",
            "price": price,
            "emoji": emoji,
            "stock_file": stock_file_path,
            "infinite_stock": False,
            "infinite_content": None,
            "sales_count": 0
        }
        vm["products"].append(new_product)
        save_json(VENDING_DATA_FILE, vending_data)
        await interaction.response.send_message(f"èªè²©æ©ã{vm['name']}ãã«ååã{name}ããè¿½å ãã¾ããã", ephemeral=True)

    @app_commands.command(name="å¨åº«è¿½å ", description="ååã®å¨åº«ãè¿½å ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="èªè²©æ©", stock_type="å¨åº«ã¿ã¤ã", stock_file="å¨åº«ãã¡ã¤ã«(txtã®ã¿)")
    @app_commands.choices(stock_type=[
        app_commands.Choice(name="æé", value="finite"),
        app_commands.Choice(name="ç¡é", value="infinite")
    ])
    async def vm_add_stock(self, interaction: discord.Interaction, vending_machine_id: str, stock_type: str, stock_file: discord.Attachment = None):
        
        if stock_file and not stock_file.filename.endswith(".txt"):
            return await interaction.response.send_message("ãã¡ã¤ã«å½¢å¼ã¯.txtã®ã¿å¯¾å¿ãã¦ãã¾ãã", ephemeral=True)

        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm or vm.get("owner_id") != str(interaction.user.id):
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)

        products = vm.get("products")
        if not products:
            return await interaction.response.send_message("å¨åº«ãè¿½å ã§ããååãããã¾ããã", ephemeral=True)
        
        view = VendingMachineCog.ProductSelectViewForStock(products, stock_file, stock_type)
        await interaction.response.send_message("å¨åº«è¿½å ãè¡ãååãé¸æãã¦ãã ãã:", view=view, ephemeral=True)

    @app_commands.command(name="èªè²©æ©è¨­ç½®", description="èªè²©æ©ããã«ãè¨­ç½®ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(
        vending_machine_id="è¨­ç½®ããèªè²©æ©", 
        panel_title="ããã«ã®ã¿ã¤ãã«",
        panel_description="ããã«ã®èª¬ææ",
        panel_image="ããã«ã®ç»å"
    )
    async def vm_setup(self, interaction: discord.Interaction, vending_machine_id: str, panel_title: str = None, panel_description: str = None, panel_image: discord.Attachment = None):
        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm:
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)

        # ã«ã¹ã¿ã ããã«ãããã©ã«ãããã«ããå¤å®
        is_custom = any([panel_title, panel_description, panel_image])
        
        if is_custom:
            # ã«ã¹ã¿ã ããã«
            title = panel_title if panel_title else "èªè²©æ©"
            description = panel_description if panel_description else "ååãé¸æãã¦ãã ãã"
            embed = discord.Embed(title=title, description=description, color=0x67A7CC,)
            
            if panel_image:
                embed.set_image(url=panel_image.url)
        else:
            # ããã©ã«ãããã«
            embed = discord.Embed(title="èªè²©æ©", description="è³¼å¥ãããååãä¸ã®ã¡ãã¥ã¼ããé¸æãã¦ãã ããã", color=0x67A7CC,)
        
        embed.set_footer(text=interaction.client.embed_footer)
        
        # ååãã£ã¼ã«ããçµ±ä¸ãã¦è¿½å 
        products = vm.get("products", [])
        if products:
            for p in products:
                price_text = f"```ä¾¡æ ¼: {p.get('price', 'æªè¨­å®')}å```"
                product_description = p.get('description', '').strip()
                if product_description:
                    value = f"{product_description}{price_text}"
                else:
                    value = price_text
                embed.add_field(
                    name=f"{p['name']}", 
                    value=value, 
                    inline=False
                )
        else:
            if not is_custom:  # ããã©ã«ãããã«ã®å ´åã®ã¿ä¸æ¸ã
                embed.description = "```ç¾å¨ãè²©å£²ä¸­ã®ååã¯ããã¾ããã```"

        view = VendingMachineCog.VendingMachineView(vending_machine_id, self.bot)
        msg = await interaction.response.send_message(embed=embed, view=view)

        vending_data[vending_machine_id]["panel_message_id"] = msg.id
        vending_data[vending_machine_id]["panel_channel_id"] = interaction.channel.id
        save_json(VENDING_DATA_FILE, vending_data)

    @app_commands.command(name="å¨åº«å¼åº", description="ååã®å¨åº«ãå¼ãåºãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="èªè²©æ©", quantity="æ°é")
    async def vm_withdraw_stock(self, interaction: discord.Interaction, vending_machine_id: str, quantity: int):
        if quantity <= 0:
            return await interaction.response.send_message("å¼åºæ°éã¯1ä»¥ä¸ã§æå®ãã¦ãã ããã", ephemeral=True)

        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm or vm.get("owner_id") != str(interaction.user.id):
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)

        products = vm.get("products")
        if not products:
            return await interaction.response.send_message("å¼åºã§ããååãããã¾ããã", ephemeral=True)
        
        view = VendingMachineCog.WithdrawStockView(products, quantity)
        await interaction.response.send_message("å¨åº«å¼åºãè¡ãååãé¸æãã¦ãã ãã:", view=view, ephemeral=True)

    @app_commands.command(name="å¨åº«åå®¹ç¢ºèª", description="ååã®å¨åº«åå®¹ãç¢ºèªãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="èªè²©æ©")
    async def vm_check_stock_content(self, interaction: discord.Interaction, vending_machine_id: str):
        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm or vm.get("owner_id") != str(interaction.user.id):
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)

        products = vm.get("products")
        if not products:
            return await interaction.response.send_message("åå®¹ãç¢ºèªã§ããååãããã¾ããã", ephemeral=True)
        
        view = VendingMachineCog.ContentView(products)
        await interaction.response.send_message("å¨åº«åå®¹ç¢ºèªãè¡ãååãé¸æãã¦ãã ãã:", view=view, ephemeral=True)

    @app_commands.command(name="åååé¤", description="èªè²©æ©ããååãå®å¨ã«åé¤ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="èªè²©æ©")
    async def vm_delete_product(self, interaction: discord.Interaction, vending_machine_id: str):
        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm or vm.get("owner_id") != str(interaction.user.id):
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)

        products = vm.get("products")
        if not products:
            return await interaction.response.send_message("åé¤ã§ããååãããã¾ããã", ephemeral=True)
        
        view = ui.View(timeout=None)
        view.add_item(VendingMachineCog.ProductSelectForDelete(products))
        
        await interaction.response.send_message("åé¤ããååãé¸æãã¦ãã ãã:", view=view, ephemeral=True)

    @app_commands.command(name="ååæå ±å¤æ´", description="ååã®åæå ±ãå¤æ´ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="èªè²©æ©")
    async def vm_edit_product(self, interaction: discord.Interaction, vending_machine_id: str):
        vending_data = load_json(VENDING_DATA_FILE)
        vm = vending_data.get(vending_machine_id)
        if not vm or vm.get("owner_id") != str(interaction.user.id):
            return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)

        products = vm.get("products")
        if not products:
            return await interaction.response.send_message("æå ±ãå¤æ´ã§ããååãããã¾ããã", ephemeral=True)
        
        view = VendingMachineCog.EditProductView(products, vending_machine_id)
        await interaction.response.send_message("æå ±ãå¤æ´ããååãé¸æãã¦ãã ãã:", view=view, ephemeral=True)

    @app_commands.command(name="èªè²©æ©åé¤", description="èªè²©æ©ãå®å¨ã«åé¤ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="åé¤ããèªè²©æ©")
    async def vm_delete(self, interaction: discord.Interaction, vending_machine_id: str):
        try:
            vending_data = load_json(VENDING_DATA_FILE)
            vm = vending_data.get(vending_machine_id)

            if not vm or vm.get("owner_id") != str(interaction.user.id):
                return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
            
            vm_name = vm.get("name", "åç§°ä¸æ")
            
            # ç¢ºèªãã¿ã³ãè¡¨ç¤º
            view = VendingMachineCog.VendingMachineDeleteConfirmView(vending_machine_id, vm_name)
            
            embed = discord.Embed(
                title="èªè²©æ©åé¤ç¢ºèª",
                description=f"æ¬å½ã«èªè²©æ©ã{vm_name}ããåé¤ãã¾ããï¼\n\n**ãã®æä½ã¯åãæ¶ãã¾ããã**\n**ãã¹ã¦ã®ååã¨å¨åº«ãã¼ã¿ãåé¤ããã¾ãã**",
                color=0x67A7CC,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=interaction.client.embed_footer)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            await handle_error(interaction, e)

    @app_commands.command(name="èªè²©æ©ããã«æ´æ°", description="èªè²©æ©ããã«ãæ´æ°ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(
        vending_machine_id="æ´æ°ããèªè²©æ©", 
        message_link="æ´æ°ããã¡ãã»ã¼ã¸ã®ãªã³ã¯",
        panel_title="ããã«ã®ã¿ã¤ãã«",
        panel_description="ããã«ã®èª¬ææ",
        panel_image="ããã«ã®ç»å"
    )
    async def vm_update(self, interaction: discord.Interaction, vending_machine_id: str, message_link: str, panel_title: str = None, panel_description: str = None, panel_image: discord.Attachment = None):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # æ¨©éãã§ãã¯
            vending_data = load_json(VENDING_DATA_FILE)
            vm = vending_data.get(vending_machine_id)
            if not vm or vm.get("owner_id") != str(interaction.user.id):
                embed = discord.Embed(
                    title="ERROR",
                    description="æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã",
                    color=0x67A7CC
                )
                embed.set_footer(text=interaction.client.embed_footer)
                return await interaction.followup.send(embed=embed, ephemeral=True)
            
            # ã¡ãã»ã¼ã¸ãªã³ã¯ãè§£æ
            try:
                # Discord ã¡ãã»ã¼ã¸ãªã³ã¯ã®å½¢å¼: https://discord.com/channels/guild_id/channel_id/message_id
                # ã¾ãã¯ https://discordapp.com/channels/guild_id/channel_id/message_id
                link_parts = message_link.replace("https://discord.com/channels/", "").replace("https://discordapp.com/channels/", "")
                guild_id, channel_id, message_id = link_parts.split("/")
                
                # ãã£ã³ãã«ã¨ã¡ãã»ã¼ã¸ãåå¾
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    embed = discord.Embed(
                        title="ERROR",
                        description="æå®ããããã£ã³ãã«ãè¦ã¤ããã¾ããã",
                        color=0x67ACC
                    )
                    embed.set_footer(text=interaction.client.embed_footer)
                    return await interaction.followup.send(embed=embed, ephemeral=True)
                
                message = await channel.fetch_message(int(message_id))
                if not message:
                    embed = discord.Embed(
                        title="ERROR",
                        description="æå®ãããã¡ãã»ã¼ã¸ãè¦ã¤ããã¾ããã",
                        color=0x67ACC
                    )
                    embed.set_footer(text=interaction.client.embed_footer)
                    return await interaction.followup.send(embed=embed, ephemeral=True)
                
                # ã¡ãã»ã¼ã¸ã®éä¿¡èããããããã§ãã¯
                if message.author.id != self.bot.user.id:
                    embed = discord.Embed(
                        title="ERROR",
                        description="æå®ãããã¡ãã»ã¼ã¸ã¯BOTãéä¿¡ãããã®ã§ã¯ããã¾ããã",
                        color=0x67ACC
                    )
                    embed.set_footer(text=interaction.client.embed_footer)
                    return await interaction.followup.send(embed=embed, ephemeral=True)
                
            except (ValueError, IndexError):
                embed = discord.Embed(
                    title="ERROR",
                    description="ã¡ãã»ã¼ã¸ãªã³ã¯ã®å½¢å¼ãæ­£ããããã¾ããã",
                    color=0x67ACC
                )
                embed.set_footer(text=interaction.client.embed_footer)
                return await interaction.followup.send(embed=embed, ephemeral=True)
            
            # æ°ããèªè²©æ©ããã«ãä½æ
            # ã«ã¹ã¿ã ããã«ãããã©ã«ãããã«ããå¤å®
            is_custom = any([panel_title, panel_description, panel_image])
            
            if is_custom:
                # ã«ã¹ã¿ã ããã«
                title = panel_title if panel_title else "èªè²©æ©"
                description = panel_description if panel_description else "è³¼å¥ãããååãä¸ã®ã¡ãã¥ã¼ããé¸æãã¦ãã ããã"
                embed = discord.Embed(title=title, description=description, color=0x67ACC)
                
                if panel_image:
                    embed.set_image(url=panel_image.url)
            else:
                # ããã©ã«ãããã«
                embed = discord.Embed(
                    title="èªè²©æ©", 
                    description="è³¼å¥ãããååãä¸ã®ã¡ãã¥ã¼ããé¸æãã¦ãã ããã", 
                    color=0x67ACC
                )
            
            embed.set_footer(text=interaction.client.embed_footer)
            
            # ååãã£ã¼ã«ããçµ±ä¸ãã¦è¿½å 
            products = vm.get("products", [])
            if products:
                for p in products:
                    price_text = f"```ä¾¡æ ¼: {p.get('price', 'æªè¨­å®')}å```"
                    product_description = p.get('description', '').strip()
                    if product_description:
                        value = f"{product_description}{price_text}"
                    else:
                        value = price_text
                    embed.add_field(
                        name=f"{p['name']}", 
                        value=value, 
                        inline=False
                    )
            else:
                if not is_custom:  # ããã©ã«ãããã«ã®å ´åã®ã¿ä¸æ¸ã
                    embed.description = "```ç¾å¨ãè²©å£²ä¸­ã®ååã¯ããã¾ããã```"
            
            # æ°ããViewãä½æ
            view = VendingMachineCog.VendingMachineView(vending_machine_id, self.bot)
            
            # ã¡ãã»ã¼ã¸ãæ´æ°
            await message.edit(embed=embed, view=view)

            embed_success = discord.Embed(
                title="æ´æ°å®äº",
                description=f"èªè²©æ©ã{vm['name']}ãã®ããã«ãæ´æ°ãã¾ããã",
                color=0x67ACC
            )
            embed.set_footer(text=interaction.client.embed_footer)
            await interaction.followup.send(embed=embed_success, ephemeral=True)
            
        except Exception as e:
            await handle_error(interaction, e)

    # æ°ããè³¼å¥ãã­ã¼ç¨ã®ã¢ã¼ãã«
    class VendingMachineDeleteConfirmView(ui.View):
        def __init__(self, vending_machine_id: str, vm_name: str):
            super().__init__(timeout=300)
            self.vending_machine_id = vending_machine_id
            self.vm_name = vm_name

        @ui.button(label="åé¤ãã", style=discord.ButtonStyle.danger)
        async def confirm_delete(self, interaction, button):
            await interaction.response.defer(ephemeral=True)
            try:
                vending_data = load_json(VENDING_DATA_FILE)
                vm = vending_data.get(self.vending_machine_id)

                if not vm or vm.get("owner_id") != str(interaction.user.id):
                    return await interaction.followup.send("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
                
                # å¨åº«ãã¡ã¤ã«ãåé¤
                for product in vm.get("products", []):
                    stock_file_path = product.get("stock_file")
                    if stock_file_path and os.path.exists(stock_file_path):
                        try:
                            os.remove(stock_file_path)
                        except Exception:
                            pass

                # èªè²©æ©ãã¼ã¿ãåé¤
                del vending_data[self.vending_machine_id]
                save_json(VENDING_DATA_FILE, vending_data)

                embed = discord.Embed(
                    title="åé¤å®äº",
                    description=f"èªè²©æ©ã{self.vm_name}ããåé¤ãã¾ããã",
                    color=0x67ACC,
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text=interaction.client.embed_footer)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                await handle_error(interaction, e)

        @ui.button(label="ã­ã£ã³ã»ã«", style=discord.ButtonStyle.secondary)
        async def cancel_delete(self, interaction, button):
            embed = discord.Embed(
                title="ã­ã£ã³ã»ã«",
                description="èªè²©æ©åé¤ãã­ã£ã³ã»ã«ãã¾ããã",
                color=0x67ACC,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=interaction.client.embed_footer)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    class CouponModal(ui.Modal, title="è³¼å¥æå ±å¥å"):
        def __init__(self, vending_machine_id: str, product: dict, bot: commands.Bot):
            super().__init__()
            self.vending_machine_id = vending_machine_id
            self.product = product
            self.bot = bot
            
            # ç¡éå¨åº«ã®å ´åã¯è³¼å¥æ°å¥åãè¡¨ç¤ºããªã
            if not product.get('infinite_stock'):
                self.quantity_input = ui.TextInput(
                    label="è³¼å¥æ°", 
                    placeholder="1", 
                    required=True, 
                    max_length=5
                )
                self.add_item(self.quantity_input)
            else:
                self.quantity_input = None
            
            self.coupon_input = ui.TextInput(
                label="ã¯ã¼ãã³ã³ã¼ã", 
                placeholder="ããã°ã¯ã¼ãã³ã³ã¼ããå¥å", 
                required=False, 
                max_length=50
            )
            self.add_item(self.coupon_input)

        async def on_submit(self, interaction):
            try:
                # ç¡éå¨åº«ã®å ´åã¯è³¼å¥æ°ã1ã«åºå®
                if self.product.get('infinite_stock'):
                    quantity = 1
                else:
                    quantity = int(self.quantity_input.value)
                    if quantity <= 0: 
                        return await interaction.response.send_message("è³¼å¥æ°ã¯1ä»¥ä¸ã§å¥åãã¦ãã ããã", ephemeral=True)
                    
            except ValueError:
                return await interaction.response.send_message("è³¼å¥æ°ã«ã¯æ´æ°ãå¥åãã¦ãã ããã", ephemeral=True)

            coupon_code = self.coupon_input.value.strip() if self.coupon_input.value else None
            
            # ã¯ã¼ãã³ã®æ¤è¨¼ã¨å²å¼è¨ç®
            discount = 0
            if coupon_code:
                coupon_data = load_coupon_data()
                if coupon_code in coupon_data:
                    coupon_info = coupon_data[coupon_code]
                    # èªè²©æ©æå®ã®ã¯ã¼ãã³ããã§ãã¯
                    if coupon_info.get("vending_machine_id") == self.vending_machine_id:
                        discount = coupon_info.get("discount", 0)
                    else:
                        return await interaction.response.send_message("ãã®ã¯ã¼ãã³ã³ã¼ãã¯ãã®èªè²©æ©ã§ã¯ä½¿ç¨ã§ãã¾ããã", ephemeral=True)
                else:
                    return await interaction.response.send_message("ç¡å¹ãªã¯ã¼ãã³ã³ã¼ãã§ãã", ephemeral=True)
            
            product_price = self.product.get('price', 0)
            # (å¤æ®µ - å²å¼) Ã åæ° ã®è¨ç®
            base_price = product_price * quantity
            total_discount = discount * quantity
            final_price = max(0, base_price - total_discount)
            
            # è³¼å¥ç¢ºèªããã«ãè¡¨ç¤º
            embed = discord.Embed(
                title="è³¼å¥ç¢ºèª",
                color=0x67ACC,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="ååå", value=f"```{self.product['name']}```", inline=False)
            
            # ç¡éå¨åº«ã®å ´åã¯åæ°è¡¨ç¤ºãå¤æ´
            if self.product.get('infinite_stock'):
                embed.add_field(name="åæ°", value=f"```1å```", inline=False)
            else:
                embed.add_field(name="åæ°", value=f"```{quantity}å```", inline=False)
            
            if discount > 0:
                embed.add_field(name="éé¡", value=f"```{product_price}å Ã {quantity}å - {discount}å Ã {quantity}å = {final_price}å```", inline=False)
            else:
                embed.add_field(name="éé¡", value=f"```{final_price}å```", inline=False)
            
            embed.set_footer(text=interaction.client.embed_footer)
            
            view = VendingMachineCog.PurchaseConfirmView(
                self.vending_machine_id, 
                self.product, 
                quantity, 
                final_price, 
                self.bot
            )
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    class PurchaseConfirmView(ui.View):
        def __init__(self, vending_machine_id: str, product: dict, quantity: int, final_price: int, bot: commands.Bot):
            super().__init__(timeout=300)
            self.vending_machine_id = vending_machine_id
            self.product = product
            self.quantity = quantity
            self.final_price = final_price
            self.bot = bot

        @ui.button(label="è³¼å¥ç¢ºå®", style=discord.ButtonStyle.green)
        async def confirm_purchase(self, interaction, button):
            if self.final_price == 0:
                # 0åååã®å ´åã¯ç´æ¥è³¼å¥å¦ç
                await self.process_purchase(interaction, None)
            else:
                # ææååã®å ´åã¯PayPayãªã³ã¯å¥åã¢ã¼ãã«ãè¡¨ç¤º
                modal = VendingMachineCog.PayPayModal(
                    self.vending_machine_id, 
                    self.product, 
                    self.quantity, 
                    self.final_price, 
                    self.bot
                )
                await interaction.response.send_modal(modal)

        async def process_purchase(self, interaction, pay_link):
            await interaction.response.defer(ephemeral=True)
            
            try:
                # èªè²©æ©ã®å­å¨ç¢ºèª
                vending_data = load_json(VENDING_DATA_FILE)
                vm = vending_data.get(self.vending_machine_id)
                if not vm:
                    embed = discord.Embed(
                        title="ã¨ã©ã¼",
                        description="ãã®èªè²©æ©ã¯åé¤ããã¦ããããå­å¨ãã¾ããã",
                        color=0x67ACC
                    )
                    embed.set_footer(text=interaction.client.embed_footer)
                    return await interaction.followup.send(embed=embed, ephemeral=True)
                
                # ææååã®å ´åã¯PayPayæ±ºæ¸å¦ç
                if self.final_price > 0:
                    payment_info = await paypayu.check_link(pay_link)
                    if not payment_info:
                        return await interaction.followup.send("æå¹ãªPayPayãªã³ã¯ãå¥åãã¦ãã ããã", ephemeral=True)

                    total_payment_amount = payment_info.get("payload", {}).get("message", {}).get("data", {}).get("amount")
                    if total_payment_amount < self.final_price:
                        return await interaction.followup.send(f"éé¡ãä¸è¶³ãã¦ãã¾ãã\nå¿è¦ãªéé¡: {self.final_price}å\nããªãã®æ¯æé¡: {total_payment_amount}å", ephemeral=True)
                    
                    paypay_data = load_paypay_data()
                    owner_credentials = paypay_data.get(vm["paypay_id"])

                    if not owner_credentials:
                        return await interaction.followup.send("è²©å£²èã®PayPayã¢ã«ã¦ã³ããè¨­å®ããã¦ãã¾ããã\nè²©å£²èã«ãåãåãããã ããã", ephemeral=True)

                    result = await paypayu.link_rev(
                        pay_link,
                        owner_credentials["phone"],
                        owner_credentials["password"],
                        owner_credentials["uuid"]
                    )
                    
                    # ã­ã°ã¢ã¦ãããã¦ããå ´åã¯èªååã­ã°ã¤ã³
                    if result == False:
                        try:
                            login_result = await paypayu.login(
                                owner_credentials["phone"],
                                owner_credentials["password"],
                                owner_credentials["uuid"]
                            )
                            
                            if login_result:
                                result = await paypayu.link_rev(
                                    pay_link,
                                    owner_credentials["phone"],
                                    owner_credentials["password"],
                                    owner_credentials["uuid"]
                                )
                        except Exception as e:
                            print(f"èªååã­ã°ã¤ã³ã¨ã©ã¼: {e}")
                    
                    if result != True:
                        return await interaction.followup.send("PayPayæ±ºæ¸ã®å¦çã«å¤±æãã¾ããããªã³ã¯ãæ­£ãããç¢ºèªãã¦ãã ããã", ephemeral=True)

                # å¨åº«å¦ç
                if self.product.get("infinite_stock"):
                    purchased_content = f"```\n{self.product.get('infinite_content', '')}\n```"
                    purchased_content_text = self.product.get('infinite_content', '')
                else:
                    with open(self.product["stock_file"], "r+", encoding="utf-8") as file:
                        lines = [line for line in file.readlines() if line.strip()]
                        
                        if len(lines) < self.quantity:
                            return await interaction.followup.send(f"å¨åº«ãä¸è¶³ãã¦ãã¾ãã\nå¿è¦æ°: {self.quantity}å\nç¾å¨ã®å¨åº«: {len(lines)}å", ephemeral=True)
                        
                        purchased_items = lines[:self.quantity]
                        remaining_items = lines[self.quantity:]
                        
                        file.seek(0)
                        file.truncate()
                        file.write("\n".join(remaining_items))
                    
                    purchased_content = f"```\n{''.join(purchased_items).strip()}\n```"
                    purchased_content_text = ''.join(purchased_items).strip()
                
                # ä¾¡æ ¼è¡¨ç¤ºãèª¿æ´
                price_display = "0å" if self.final_price == 0 else f"{self.final_price}å"
                
                embed = discord.Embed(
                    title="è³¼å¥å®äº",
                    description=f"**åå:** `{self.product['name']}`\n**æ°é:** `{self.quantity}`å\n**åè¨éé¡:** `{price_display}`",
                    color=0x67ACC,
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="è³¼å¥ããåå", value=purchased_content, inline=False)
                embed.set_footer(text=interaction.client.embed_footer)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # è²©å£²æ°ãå¢ããå¦ç
                vending_data = load_json(VENDING_DATA_FILE)
                for vm_id, vm_data in vending_data.items():
                    for i, p in enumerate(vm_data.get("products", [])):
                        if p["product_id"] == self.product["product_id"]:
                            current_sales = p.get("sales_count", 0)
                            vm_data["products"][i]["sales_count"] = current_sales + self.quantity
                            break
                save_json(VENDING_DATA_FILE, vending_data)
                
                # ã­ã¼ã«ä»ä¸å¦ç
                try:
                    role_data = load_role_assignment_data()
                    role_info = role_data.get(self.vending_machine_id)
                    if role_info and role_info.get("guild_id") == interaction.guild.id:
                        role = interaction.guild.get_role(role_info.get("role_id"))
                        if role and role not in interaction.user.roles:
                            await interaction.user.add_roles(role)
                except:
                    pass  # ã­ã¼ã«ä»ä¸ã¨ã©ã¼ã¯ç¡è¦
                
                # DMã§è³¼å¥åå®¹ãéä¿¡
                try:
                    import datetime
                    import pytz
                    
                    jst = pytz.timezone('Asia/Tokyo')
                    now_jst = datetime.datetime.now(jst)
                    formatted_time = now_jst.strftime("%Y/%m/%d %H:%M:%S(JST)")
                    
                    dm_embed = discord.Embed(
                        title="è³¼å¥ãå®äºãã¾ãã",
                        color=0x67ACC,
                        timestamp=discord.utils.utcnow()
                    )
                    dm_embed.add_field(name="è³¼å¥æ¥", value=f"```{formatted_time}```", inline=True)
                    dm_embed.add_field(name="è³¼å¥ãµã¼ãã¼", value=f"```{interaction.guild.name}({interaction.guild.id})```", inline=True)
                    dm_embed.add_field(name="ååå", value=f"```{self.product['name']}```", inline=True)
                    dm_embed.add_field(name="è³¼å¥æ°", value=f"```{self.quantity}å```", inline=True)
                    dm_embed.add_field(name="æ¯æéé¡", value=f"```{price_display}```", inline=True)
                    dm_embed.set_footer(text="èªè²©æ©è£½ä½è ããµã")
                    
                    await interaction.user.send(purchased_content_text, embed=dm_embed)
                except:
                    pass
                
                # å¬éã­ã°éä¿¡
                if vm.get("log_channel_id"):
                    log_channel = self.bot.get_channel(vm["log_channel_id"])
                    if log_channel:
                        colors = [
                          0xADE0EE,
                          0x007DC5,
                          0x00AE95
                        ]
                        random_color = random.choice(colors)
                        
                        log_embed = discord.Embed(color=random_color)
                        log_embed.add_field(name="ååå", value=f"```{self.product['name']}```", inline=True)
                        log_embed.add_field(name="è³¼å¥æ°", value=f"```{self.quantity}å```", inline=True)
                        log_embed.add_field(name="è³¼å¥ãµã¼ãã¼", value=f"```{interaction.guild.name}({interaction.guild.id})```", inline=True)
                        log_embed.add_field(name="è³¼å¥è", value=f"{interaction.user.mention}({interaction.user.id})", inline=True)
                        log_embed.set_footer(text=interaction.client.embed_footer)
                        await log_channel.send(embed=log_embed)
                
                # éå¬éã­ã°éä¿¡
                if vm.get("private_log_channel_id"):
                    private_log_channel = self.bot.get_channel(vm["private_log_channel_id"])
                    if private_log_channel:
                        private_log_embed = discord.Embed(color=discord.Color.orange())
                        private_log_embed.add_field(name="ååå", value=f"```{self.product['name']}```", inline=True)
                        private_log_embed.add_field(name="è³¼å¥æ°", value=f"```{self.quantity}å```", inline=True)
                        private_log_embed.add_field(name="è³¼å¥ãµã¼ãã¼", value=f"```{interaction.guild.name}({interaction.guild.id})```", inline=True)
                        private_log_embed.add_field(name="è³¼å¥è", value=f"{interaction.user.mention}({interaction.user.id})", inline=True)
                        private_log_embed.add_field(name="æ¯æéé¡", value=f"```{price_display}```", inline=True)
                        private_log_embed.add_field(name="èªè²©æ©", value=f"```{vm['name']}({self.vending_machine_id})```", inline=True)
                        private_log_embed.set_footer(text=interaction.client.embed_footer)
                        
                        discord_file = discord.File(
                            io.BytesIO(purchased_content_text.encode('utf-8')),
                            filename=f"purchase_{interaction.user.id}_{int(discord.utils.utcnow().timestamp())}.txt"
                        )
                        
                        await private_log_channel.send(embed=private_log_embed, file=discord_file)
                
            except Exception as e:
                await handle_error(interaction, e)

    class PayPayModal(ui.Modal, title="PayPayæ±ºæ¸"):
        def __init__(self, vending_machine_id: str, product: dict, quantity: int, final_price: int, bot: commands.Bot):
            super().__init__()
            self.vending_machine_id = vending_machine_id
            self.product = product
            self.quantity = quantity
            self.final_price = final_price
            self.bot = bot
            
            self.paypay_input = ui.TextInput(
                label="PayPayãªã³ã¯", 
                placeholder="https://pay.paypay.ne.jp/...", 
                required=True
            )
            self.add_item(self.paypay_input)

        async def on_submit(self, interaction):
            # PurchaseConfirmViewã®process_purchaseã¡ã½ãããå¼ã³åºã
            confirm_view = VendingMachineCog.PurchaseConfirmView(
                self.vending_machine_id, 
                self.product, 
                self.quantity, 
                self.final_price, 
                self.bot
            )
            await confirm_view.process_purchase(interaction, self.paypay_input.value)

    class ProductSelect(ui.Select):
        def __init__(self, vending_machine_id: str, bot: commands.Bot):
            self.vending_machine_id = vending_machine_id
            self.bot = bot
            
            # ææ°ã®ååãã¼ã¿ãåå¾
            vending_data = load_json(VENDING_DATA_FILE)
            vm = vending_data.get(vending_machine_id, {})
            products = vm.get("products", [])
            
            options = []
            if products:
                for product in products:
                    emoji = product.get("emoji")
                    label = f"{product['name']}"
                    
                    # å¨åº«æ°ã¨è²©å£²æ°ãåå¾
                    sales_count = product.get("sales_count", 0)
                    if product.get("infinite_stock"):
                        description = f"ä¾¡æ ¼: {product['price']}åâå¨åº«æ°: âåâè²©å£²æ°: {sales_count}å"
                    else:
                        try:
                            with open(product.get("stock_file", ""), "r", encoding="utf-8") as f:
                                lines = [line for line in f.readlines() if line.strip()]
                                stock_count = len(lines)
                        except:
                            stock_count = 0
                        
                        description = f"ä¾¡æ ¼: {product['price']}åâå¨åº«æ°: {stock_count}åâè²©å£²æ°: {sales_count}å"
                    
                    options.append(discord.SelectOption(
                        label=label,
                        value=product["product_id"],
                        description=description,
                        emoji=emoji
                    ))
            
            if not options:
                options.append(discord.SelectOption(label="ååãªã", value="none", description="ç¾å¨è²©å£²ä¸­ã®ååã¯ããã¾ãã"))
            
            super().__init__(
                placeholder="ååãé¸æãã",
                options=options,
                custom_id=f"product_select_{vending_machine_id}"
            )

        async def callback(self, interaction):
            if self.values[0] == "none":
                return await interaction.response.send_message("ç¾å¨è²©å£²ä¸­ã®ååã¯ããã¾ããã", ephemeral=True)
            
            try:
                # èªè²©æ©ã®å­å¨ç¢ºèª
                vending_data = load_json(VENDING_DATA_FILE)
                vm = vending_data.get(self.vending_machine_id, {})
                if not vm:
                    embed = discord.Embed(
                        title="ã¨ã©ã¼",
                        description="ãã®èªè²©æ©ã¯åé¤ããã¦ããããå­å¨ãã¾ããã",
                        color=0x67ACC
                    )
                    embed.set_footer(text=interaction.client.embed_footer)
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                
                products = vm.get("products", [])
                product = next((p for p in products if p["product_id"] == self.values[0]), None)
                if not product: 
                    return await interaction.response.send_message("ååãè¦ã¤ããã¾ããã", ephemeral=True)
                
                # å¨åº«ãã§ãã¯
                if product.get("infinite_stock"):
                    # ç¡éå¨åº«ã®å ´åã¯å¸¸ã«è³¼å¥å¯è½
                    modal = VendingMachineCog.CouponModal(self.vending_machine_id, product, self.bot)
                    await interaction.response.send_modal(modal)
                else:
                    # æéå¨åº«ã®å ´å
                    try:
                        with open(product.get("stock_file", ""), "r", encoding="utf-8") as f:
                            lines = [line for line in f.readlines() if line.strip()]
                            if len(lines) == 0:
                                embed = discord.Embed(
                                    title="å¨åº«ä¸è¶³",
                                    description=f"ç¾å¨ {product['name']}ã®å¨åº«ãä¸è¶³ãã¦ãã¾ãã",
                                    color=0x67ACC
                                )
                                embed.set_footer(text="èªè²©æ©è£½ä½è ããµã")
                                return await interaction.response.send_message(embed=embed, ephemeral=True)
                    except:
                        embed = discord.Embed(
                            title="å¨åº«ä¸è¶³",
                            description=f"ç¾å¨ {product['name']}ã®å¨åº«ãä¸è¶³ãã¦ãã¾ãã",
                            color=0x67ACC
                        )
                        embed.set_footer(text=interaction.client.embed_footer)
                        return await interaction.response.send_message(embed=embed, ephemeral=True)
                    
                    modal = VendingMachineCog.CouponModal(self.vending_machine_id, product, self.bot)
                    await interaction.response.send_modal(modal)
                
            except Exception as e:
                await handle_error(interaction, e)

    class PurchaseButton(ui.Button):
        def __init__(self, vending_machine_id: str, bot: commands.Bot):
            super().__init__(
                label="è³¼å¥ãã",
                style=discord.ButtonStyle.green,
                emoji="ð",
                custom_id=f"purchase_{vending_machine_id}",
                row=0
            )

            self.vending_machine_id = vending_machine_id
            self.bot = bot

        async def callback(self, interaction):
            try:
                embed = discord.Embed(
                    title="è³¼å¥ããååãé¸æãã¦ãã ããã",
                    color=discord.Color.green()
                )
                view = VendingMachineCog.ProductSelectView(self.vending_machine_id, self.bot)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            except Exception as e:
                await handle_error(interaction, e)

    class ProductSelectView(ui.View):
        def __init__(self, vending_machine_id: str, bot: commands.Bot):
            super().__init__(timeout=180)
            self.vending_machine_id = vending_machine_id
            self.add_item(VendingMachineCog.ProductSelect(vending_machine_id, bot))

    class StockCheckButton(discord.ui.Button):
        def __init__(self, vending_machine_id, row=None):
            super().__init__(
                label="å¨åº«ã»è²©å£²æ°ç¢ºèª",
                style=discord.ButtonStyle.primary,
                emoji="ð¦",
                custom_id=f"check_stock_{vending_machine_id}",
                row=0
            )

            self.vending_machine_id = vending_machine_id

        async def callback(self, interaction):
            try:
                # èªè²©æ©ã®å­å¨ç¢ºèª
                vending_data = load_json(VENDING_DATA_FILE)
                vm = vending_data.get(self.vending_machine_id, {})
                if not vm:
                    embed = discord.Embed(
                        title="ã¨ã©ã¼",
                        description="ãã®èªè²©æ©ã¯åé¤ããã¦ããããå­å¨ãã¾ããã",
                        color=0x67ACC
                    )
                    embed.set_footer(text=interaction.client.embed_footer)
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # ææ°ã®ååãã¼ã¿ãåçã«åå¾
                products = vm.get("products", [])
                await interaction.response.defer(ephemeral=True)
                await check_stock(interaction, products)
            except Exception as e:
                await handle_error(interaction, e)

    class VendingMachineView(discord.ui.View):
        def __init__(self, vending_machine_id: str, bot):
            super().__init__(timeout=None)

            self.add_item(
                VendingMachineCog.PurchaseButton(vending_machine_id, bot)
            )

            self.add_item(
                VendingMachineCog.StockCheckButton(vending_machine_id)
            )

    class ProductSelectViewForStock(ui.View):
        def __init__(self, products: list, attachment: discord.Attachment = None, stock_type: str = "finite"):
            super().__init__(timeout=None)
            self.add_item(VendingMachineCog.ProductSelectForStock(products, attachment, stock_type))
            
    class ProductSelectForStock(ui.Select):
        def __init__(self, products: list, attachment: discord.Attachment = None, stock_type: str = "finite"):
            self.products = products
            self.attachment = attachment
            self.stock_type = stock_type
            options = [discord.SelectOption(label=p["name"], value=p["product_id"]) for p in products]
            super().__init__(
                placeholder="å¨åº«ãè¿½å ããååãé¸æ...", 
                options=options,
                custom_id="stock_add_select"
            )

        async def callback(self, interaction):
            try:
                product = next((p for p in self.products if p["product_id"] == self.values[0]), None)
                if not product:
                    await interaction.response.send_message("ååãè¦ã¤ããã¾ããã", ephemeral=True)
                    return

                if self.stock_type == "infinite":
                    # ç¡éå¨åº«ã®å ´å
                    if self.attachment:
                        await interaction.response.defer(ephemeral=True)
                        try:
                            new_stock_content = await self.attachment.read()
                            infinite_content = new_stock_content.decode('utf-8').strip()
                            
                            # ååãã¼ã¿ãæ´æ°
                            vending_data = load_json(VENDING_DATA_FILE)
                            for vm_id, vm_data in vending_data.items():
                                for i, p in enumerate(vm_data.get("products", [])):
                                    if p["product_id"] == product["product_id"]:
                                        vm_data["products"][i]["infinite_stock"] = True
                                        vm_data["products"][i]["infinite_content"] = infinite_content
                                        break
                            save_json(VENDING_DATA_FILE, vending_data)
                            
                            await interaction.followup.send(f"ååã{product['name']}ããç¡éå¨åº«ã«è¨­å®ãã¾ããã", ephemeral=True)
                        except Exception as e:
                            await handle_error(interaction, e)
                    else:
                        modal = VendingMachineCog.InfiniteStockModal(product)
                        await interaction.response.send_modal(modal)
                else:
                    # æéå¨åº«ã®å ´åï¼å¾æ¥éãï¼
                    if self.attachment:
                        await interaction.response.defer(ephemeral=True)
                        try:
                            new_stock_content = await self.attachment.read()
                            new_stock_lines = [line for line in new_stock_content.decode('utf-8').splitlines() if line.strip()]
                            with open(product["stock_file"], "a", encoding="utf-8") as f:
                                if os.path.getsize(product["stock_file"]) > 0: f.write("\n")
                                f.write("\n".join(new_stock_lines))
                            
                            await interaction.followup.send(f"ååã{product['name']}ãã«`{len(new_stock_lines)}`åã®å¨åº«ãè¿½å ãã¾ããã", ephemeral=True)
                            await VendingMachineCog.refresh_panel(interaction.client, vending_machine_id)
                            # å¨åº«è¿½å éç¥ãéä¿¡
                            await self.send_stock_notification(interaction, product, len(new_stock_lines))
                            await VendingMachineCog.refresh_panel(self.view.bot, vending_machine_id)
                        except Exception as e:
                            await handle_error(interaction, e)
                    else:
                        modal = VendingMachineCog.StockAddModal(product)
                        await interaction.response.send_modal(modal)
            except Exception as e:
                await handle_error(interaction, e)
        
        async def send_stock_notification(self, interaction, product, added_count):
            try:
                # èªè²©æ©IDãåå¾
                vending_data = load_json(VENDING_DATA_FILE)
                vending_machine_id = None
                for vm_id, vm_data in vending_data.items():
                    for p in vm_data.get("products", []):
                        if p["product_id"] == product["product_id"]:
                            vending_machine_id = vm_id
                            break
                    if vending_machine_id:
                        break
                
                if not vending_machine_id:
                    return
                
                # éç¥è¨­å®ãç¢ºèª
                notification_data = load_stock_notification_data()
                notification_info = notification_data.get(vending_machine_id)
                
                if notification_info and notification_info.get("guild_id") == interaction.guild.id:
                    channel = interaction.guild.get_channel(notification_info.get("channel_id"))
                    role = interaction.guild.get_role(notification_info.get("role_id"))
                    
                    if channel and role:
                        embed = discord.Embed(
                            title="å¨åº«è¿½å éç¥",
                            color=0x67ACC,
                            timestamp=discord.utils.utcnow()
                        )
                        embed.add_field(name="è¿½å åå", value=f"```{product['name']}```", inline=True)
                        embed.add_field(name="è¿½å æ°", value=f"```{added_count}å```", inline=True)
                        embed.set_footer(text=interaction.client.embed_footer)
                        
                        await channel.send(f"{role.mention}", embed=embed)
                        
            except Exception as e:
                print(f"å¨åº«è¿½å éç¥éä¿¡ã¨ã©ã¼: {e}")

    class StockAddModal(ui.Modal, title="å¨åº«è¿½å "):
        def __init__(self, product: dict):
            super().__init__(timeout=None)
            self.product = product

        stock_input = ui.TextInput(
            label="å¨åº«åå®¹",
            style=discord.TextStyle.long,
            placeholder="è¿½å ããå¨åº«ã1è¡ãã¤å¥åãã¦ãã ãã",
            required=True
        )

        async def on_submit(self, interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                new_stock_lines = [line for line in self.stock_input.value.splitlines() if line.strip()]
                
                with open(self.product["stock_file"], "a", encoding="utf-8") as f:
                    if os.path.getsize(self.product["stock_file"]) > 0: 
                        f.write("\n")
                    f.write("\n".join(new_stock_lines))
                
                await interaction.followup.send(f"ååã{self.product['name']}ãã«`{len(new_stock_lines)}`åã®å¨åº«ãè¿½å ãã¾ããã", ephemeral=True)
                
                # å¨åº«è¿½å éç¥ãéä¿¡
                await self.send_stock_notification(interaction, self.product, len(new_stock_lines))
                
            except Exception as e:
                await handle_error(interaction, e)
        
        async def send_stock_notification(self, interaction, product, added_count):
            try:
                # èªè²©æ©IDãåå¾
                vending_data = load_json(VENDING_DATA_FILE)
                vending_machine_id = None
                for vm_id, vm_data in vending_data.items():
                    for p in vm_data.get("products", []):
                        if p["product_id"] == product["product_id"]:
                            vending_machine_id = vm_id
                            break
                    if vending_machine_id:
                        break
                
                if not vending_machine_id:
                    return
                
                # éç¥è¨­å®ãç¢ºèª
                notification_data = load_stock_notification_data()
                notification_info = notification_data.get(vending_machine_id)
                
                if notification_info and notification_info.get("guild_id") == interaction.guild.id:
                    channel = interaction.guild.get_channel(notification_info.get("channel_id"))
                    role = interaction.guild.get_role(notification_info.get("role_id"))
                    
                    if channel and role:
                        embed = discord.Embed(
                            title="å¨åº«è¿½å éç¥",
                            color=0x67ACC,
                            timestamp=discord.utils.utcnow()
                        )
                        embed.add_field(name="è¿½å åå", value=f"```{product['name']}```", inline=True)
                        embed.add_field(name="è¿½å æ°", value=f"```{added_count}å```", inline=True)
                        embed.set_footer(text=interaction.client.embed_footer)
                        
                        await channel.send(f"{role.mention}", embed=embed)
                        
            except Exception as e:
                print(f"å¨åº«è¿½å éç¥éä¿¡ã¨ã©ã¼: {e}")

    class InfiniteStockModal(ui.Modal, title="ç¡éå¨åº«è¨­å®"):
        def __init__(self, product: dict):
            super().__init__(timeout=None)
            self.product = product

        stock_input = ui.TextInput(
            label="ç¡éå¨åº«åå®¹",
            style=discord.TextStyle.long,
            placeholder="è³¼å¥æã«éä¿¡ãããåå®¹ãå¥åãã¦ãã ãã",
            required=True
        )

        async def on_submit(self, interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                infinite_content = self.stock_input.value.strip()
                
                # ååãã¼ã¿ãæ´æ°
                vending_data = load_json(VENDING_DATA_FILE)
                for vm_id, vm_data in vending_data.items():
                    for i, p in enumerate(vm_data.get("products", [])):
                        if p["product_id"] == self.product["product_id"]:
                            vm_data["products"][i]["infinite_stock"] = True
                            vm_data["products"][i]["infinite_content"] = infinite_content
                            break
                save_json(VENDING_DATA_FILE, vending_data)
                
                await interaction.followup.send(f"ååã{self.product['name']}ããç¡éå¨åº«ã«è¨­å®ãã¾ããã", ephemeral=True)
            except Exception as e:
                await handle_error(interaction, e)

    class WithdrawStockView(ui.View):
        def __init__(self, products: list, quantity: int):
            super().__init__(timeout=None)
            self.add_item(VendingMachineCog.ProductSelectForWithdraw(products, quantity))

    class ProductSelectForWithdraw(ui.Select):
        def __init__(self, products: list, quantity: int):
            self.products = products
            self.quantity = quantity
            options = [discord.SelectOption(label=p["name"], value=p["product_id"]) for p in products]
            super().__init__(
                placeholder="å¨åº«ãå¼ãåºãååãé¸æ...", 
                options=options,
                custom_id="withdraw_select"
            )

        async def callback(self, interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                product = next((p for p in self.products if p["product_id"] == self.values[0]), None)
                if not product:
                    await interaction.followup.send("ååãè¦ã¤ããã¾ããã", ephemeral=True)
                    return

                if product.get("infinite_stock"):
                    # ç¡éå¨åº«ã®å ´åã¯ç¡éå¨åº«ãè§£é¤
                    vending_data = load_json(VENDING_DATA_FILE)
                    for vm_id, vm_data in vending_data.items():
                        for i, p in enumerate(vm_data.get("products", [])):
                            if p["product_id"] == product["product_id"]:
                                withdrawn_content = f"`{p.get('infinite_content', '')}\n`"
                                vm_data["products"][i]["infinite_stock"] = False
                                vm_data["products"][i]["infinite_content"] = None
                                break
                    save_json(VENDING_DATA_FILE, vending_data)
                    
                    embed = discord.Embed(
                        title="ç¡éå¨åº«è§£é¤å®äº",
                        description=f"**åå:** `{product['name']}`\n**è§£é¤ãããç¡éå¨åº«åå®¹:**",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="å¼ãåºããç¡éå¨åº«", value=withdrawn_content, inline=False)
                    embed.set_footer(text=interaction.client.embed_footer)
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    # æéå¨åº«ã®å ´åï¼å¾æ¥éãï¼
                    try:
                        with open(product["stock_file"], "r+", encoding="utf-8") as file:
                            lines = [line for line in file.readlines() if line.strip()]
                            
                            if len(lines) < self.quantity:
                                await interaction.followup.send(f"å¨åº«ãä¸è¶³ãã¦ãã¾ãã\nå¼åºå¸ææ°: {self.quantity}å\nç¾å¨ã®å¨åº«: {len(lines)}å", ephemeral=True)
                                return
                            
                            withdrawn_items = lines[:self.quantity]
                            remaining_items = lines[self.quantity:]
                            
                            file.seek(0)
                            file.truncate()
                            file.write("\n".join(remaining_items))
                        
                        withdrawn_content = f"`{''.join(withdrawn_items).strip()}\n`"
                        
                        embed = discord.Embed(
                            title="å¨åº«å¼åºå®äº",
                            description=f"**åå:** `{product['name']}`\n**å¼åºæ°é:** `{self.quantity}`å",
                            color=0x67ACC,
                            timestamp=discord.utils.utcnow()
                        )
                        embed.add_field(name="å¼ãåºããå¨åº«", value=withdrawn_content, inline=False)
                        embed.set_footer(text=interaction.client.embed_footer)
                        
                        await interaction.followup.send(embed=embed, ephemeral=True)

                    except FileNotFoundError:
                        await handle_error(interaction, FileNotFoundError("å¨åº«ãã¡ã¤ã«ãè¦ã¤ããã¾ããã"))
                    except Exception as e:
                        await handle_error(interaction, e)
            except Exception as e:
                await handle_error(interaction, e)

    class ContentView(ui.View):
        def __init__(self, products: list):
            super().__init__(timeout=None)
            self.add_item(VendingMachineCog.ProductSelectForContent(products))

    class ProductSelectForContent(ui.Select):
        def __init__(self, products: list):
            self.products = products
            options = [discord.SelectOption(label=p["name"], value=p["product_id"]) for p in products]
            super().__init__(
                placeholder="å¨åº«åå®¹ãç¢ºèªããååãé¸æ...", 
                options=options,
                custom_id="content_select"
            )

        async def callback(self, interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                product = next((p for p in self.products if p["product_id"] == self.values[0]), None)
                if not product:
                    await interaction.followup.send("ååãè¦ã¤ããã¾ããã", ephemeral=True)
                    return

                if product.get("infinite_stock"):
                    # ç¡éå¨åº«ã®å ´å
                    infinite_content = product.get("infinite_content", "")
                    stock_content = f"`{infinite_content}\n`"
                    
                    embed = discord.Embed(
                        title="å¨åº«åå®¹",
                        description=f"**åå:** `{product['name']}`\n**å¨åº«æ°:** `â`å",
                        color=discord.Color.blue(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="ç¡éå¨åº«åå®¹", value=stock_content, inline=False)
                    embed.set_footer(text=interaction.client.embed_footer)
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    # æéå¨åº«ã®å ´åï¼å¾æ¥éãï¼
                    try:
                        with open(product["stock_file"], "r", encoding="utf-8") as file:
                            content = file.read().strip()
                            
                            if not content:
                                embed = discord.Embed(
                                    title="å¨åº«åå®¹",
                                    description=f"**åå:** `{product['name']}`\n**å¨åº«æ°:** `0`å",
                                    color=discord.Color.blue(),
                                    timestamp=discord.utils.utcnow()
                                )
                                embed.add_field(name="å¨åº«åå®¹", value="```\nå¨åº«ãããã¾ãã\n```", inline=False)
                            else:
                                lines = [line for line in content.splitlines() if line.strip()]
                                stock_content = f"`{content}`\n"
                                
                                embed = discord.Embed(
                                    title="å¨åº«åå®¹",
                                    description=f"**åå:** `{product['name']}`\n**å¨åº«æ°:** `{len(lines)}`å",
                                    color=0x67ACC,
                                    timestamp=discord.utils.utcnow()
                                )
                                embed.add_field(name="å¨åº«åå®¹", value=stock_content, inline=False)
                            
                            embed.set_footer(text=interaction.client.embed_footer)
                            await interaction.followup.send(embed=embed, ephemeral=True)

                    except FileNotFoundError:
                        await handle_error(interaction, FileNotFoundError("å¨åº«ãã¡ã¤ã«ãè¦ã¤ããã¾ããã"))
                    except Exception as e:
                        await handle_error(interaction, e)
            except Exception as e:
                await handle_error(interaction, e)

    class ProductSelectForDelete(ui.Select):
        def __init__(self, products: list):
            self.products = products
            options = [discord.SelectOption(label=p["name"], value=p["product_id"]) for p in products]
            super().__init__(
                placeholder="åé¤ããååãé¸æ...", 
                options=options,
                custom_id="delete_select"
            )

        async def callback(self, interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                product = next((p for p in self.products if p["product_id"] == self.values[0]), None)
                if not product:
                    await interaction.followup.send("ååãè¦ã¤ããã¾ããã", ephemeral=True)
                    return

                # ç¢ºèªãã¿ã³ãè¡¨ç¤º
                view = VendingMachineCog.DeleteConfirmView(product)
                
                embed = discord.Embed(
                    title="åååé¤ç¢ºèª",
                    description=f"æ¬å½ã«ååã{product['name']}ããåé¤ãã¾ããï¼\n\n**ãã®æä½ã¯åãæ¶ãã¾ããã**",
                    color=0x67ACC
                )
                embed.set_footer(text=interaction.client.embed_footer)
                
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                
            except Exception as e:
                await handle_error(interaction, e)

    class ProductDeleteView(ui.View):
        def __init__(self, products: list, vending_machine_id: str):
            super().__init__(timeout=None)
            self.vending_machine_id = vending_machine_id
            self.add_item(VendingMachineCog.ProductSelectForDelete(products))

    class DeleteConfirmView(ui.View):
        def __init__(self, product: dict):
            super().__init__(timeout=None)
            self.product = product

        @ui.button(label="åé¤ãã", style=discord.ButtonStyle.danger)
        async def confirm_delete(self, interaction, button):
            await interaction.response.defer(ephemeral=True)
            try:
                vending_data = load_json(VENDING_DATA_FILE)
                
                # ååãåé¤
                for vm_id, vm_data in vending_data.items():
                    products = vm_data.get("products", [])
                    vm_data["products"] = [p for p in products if p["product_id"] != self.product["product_id"]]
                
                save_json(VENDING_DATA_FILE, vending_data)
                
                # å¨åº«ãã¡ã¤ã«ãåé¤
                try:
                    if os.path.exists(self.product["stock_file"]):
                        os.remove(self.product["stock_file"])
                except:
                    pass
                
                embed = discord.Embed(
                    title="åé¤å®äº",
                    description=f"ååã{self.product['name']}ããåé¤ãã¾ããã",
                    color=0x67ACC
                )
                embed.set_footer(text=interaction.client.embed_footer)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            except Exception as e:
                await handle_error(interaction, e)

        @ui.button(label="ã­ã£ã³ã»ã«", style=discord.ButtonStyle.secondary)
        async def cancel_delete(self, interaction, button):
            embed = discord.Embed(
                title="ã­ã£ã³ã»ã«",
                description="åååé¤ãã­ã£ã³ã»ã«ãã¾ããã",
                color=0x67ACC
            )
            embed.set_footer(text=interaction.client.embed_footer)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    class EditProductView(ui.View):
        def __init__(self, products: list, vending_machine_id: str):
            super().__init__(timeout=None)
            self.vending_machine_id = vending_machine_id
            self.add_item(VendingMachineCog.ProductSelectForEdit(products, vending_machine_id))

    class ProductSelectForEdit(ui.Select):
        def __init__(self, products: list, vending_machine_id: str):
            self.products = products
            self.vending_machine_id = vending_machine_id
            options = [discord.SelectOption(label=p["name"], value=p["product_id"]) for p in products]
            super().__init__(
                placeholder="ç·¨éããååãé¸æ...", 
                options=options,
                custom_id="edit_select"
            )

        async def callback(self, interaction):
            try:
                product = next((p for p in self.products if p["product_id"] == self.values[0]), None)
                if not product:
                    await interaction.response.send_message("ååãè¦ã¤ããã¾ããã", ephemeral=True)
                    return

                modal = VendingMachineCog.EditProductModal(product, self.vending_machine_id)
                await interaction.response.send_modal(modal)
                
            except Exception as e:
                await handle_error(interaction, e)

    class EditProductModal(ui.Modal, title="ååæå ±ç·¨é"):
        def __init__(self, product: dict, vending_machine_id: str):
            super().__init__(timeout=None)
            self.product = product
            self.vending_machine_id = vending_machine_id
            
            # ããã©ã«ãå¤ãè¨­å®
            self.name_input.default = product.get("name", "")
            self.description_input.default = product.get("description", "")
            self.price_input.default = str(product.get("price", 0))
            self.emoji_input.default = product.get("emoji", "")

        name_input = ui.TextInput(
            label="ååå",
            placeholder="æ°ããåååãå¥å...",
            required=False,
            max_length=100
        )
        
        description_input = ui.TextInput(
            label="ååèª¬æ",
            style=discord.TextStyle.long,
            placeholder="æ°ããååèª¬æãå¥å...",
            required=False,
            max_length=1000
        )
        
        price_input = ui.TextInput(
            label="ä¾¡æ ¼",
            placeholder="æ°ããä¾¡æ ¼ãå¥å...",
            required=False,
            max_length=10
        )
        
        emoji_input = ui.TextInput(
            label="çµµæå­",
            placeholder="æ°ããçµµæå­ãå¥å...",
            required=False,
            max_length=50
        )

        async def on_submit(self, interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                vending_data = load_json(VENDING_DATA_FILE)
                updated_fields = []
                
                # ååãã¼ã¿ãæ´æ°
                for vm_id, vm_data in vending_data.items():
                    for i, p in enumerate(vm_data.get("products", [])):
                        if p["product_id"] == self.product["product_id"]:
                            if self.name_input.value.strip():
                                vm_data["products"][i]["name"] = self.name_input.value.strip()
                                updated_fields.append("ååå")
                            
                            # èª¬ææã®å¦ç
                            if self.description_input.value is not None:
                                if self.description_input.value.strip() == "":
                                    # ç©ºæå­ãæç¤ºçã«å¥åãããå ´å
                                    vm_data["products"][i]["description"] = ""
                                    updated_fields.append("èª¬æ: åé¤ããã¾ãã")
                                else:
                                    vm_data["products"][i]["description"] = self.description_input.value.strip()
                                    updated_fields.append("ååèª¬æ")
                            
                            if self.price_input.value.strip():
                                try:
                                    new_price = int(self.price_input.value.strip())
                                    if new_price >= 0:
                                        vm_data["products"][i]["price"] = new_price
                                        updated_fields.append("ä¾¡æ ¼")
                                    else:
                                        await interaction.followup.send("ä¾¡æ ¼ã¯0ä»¥ä¸ã§å¥åãã¦ãã ããã", ephemeral=True)
                                        return
                                except ValueError:
                                    await interaction.followup.send("ä¾¡æ ¼ã«ã¯æ´æ°ãå¥åãã¦ãã ããã", ephemeral=True)
                                    return
                            
                            if self.emoji_input.value.strip():
                                vm_data["products"][i]["emoji"] = self.emoji_input.value.strip()
                                updated_fields.append("çµµæå­")
                            
                            break
                
                if updated_fields:
                    save_json(VENDING_DATA_FILE, vending_data)
                    embed = discord.Embed(
                        title="ååæå ±æ´æ°å®äº",
                        description=f"ååã{self.product['name']}ãã®ä»¥ä¸ã®æå ±ãæ´æ°ãã¾ãã:\nâ¢ " + "\nâ¢ ".join(updated_fields),
                        color=0x67ACC
                    )
                    embed.set_footer(text=interaction.client.embed_footer)
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("æ´æ°ããé ç®ãå¥åããã¦ãã¾ããã", ephemeral=True)
                
            except Exception as e:
                await handle_error(interaction, e)

    @app_commands.command(name="å¨åº«è¿½å éç¥è¨­å®", description="å¨åº«è¿½å æã®éç¥è¨­å®ãè¡ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(
        vending_machine_id="éç¥è¨­å®ããèªè²©æ©",
        channel="éç¥ãéä¿¡ãããã£ã³ãã«",
        role="ã¡ã³ã·ã§ã³ããã­ã¼ã«"
    )
    async def stock_notification_setup(self, interaction, vending_machine_id: str, channel: discord.TextChannel, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        
        try:
            vending_data = load_json(VENDING_DATA_FILE)
            vm = vending_data.get(vending_machine_id)
            if not vm or vm.get("owner_id") != str(interaction.user.id):
                await interaction.followup.send("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
                return
            
            # éç¥è¨­å®ãä¿å­
            notification_data = load_stock_notification_data()
            notification_data[vending_machine_id] = {
                "channel_id": channel.id,
                "role_id": role.id,
                "guild_id": interaction.guild.id
            }
            save_stock_notification_data(notification_data)
            
            embed = discord.Embed(
                title="å¨åº«è¿½å éç¥è¨­å®",
                description=f"èªè²©æ©ã{vm['name']}ãã®å¨åº«è¿½å éç¥ãè¨­å®ãã¾ããã",
                color=0x67ACC
            )
            embed.add_field(name="éç¥ãã£ã³ãã«", value=channel.mention, inline=True)
            embed.add_field(name="ã¡ã³ã·ã§ã³ã­ã¼ã«", value=role.mention, inline=True)
            embed.set_footer(text=interaction.client.embed_footer)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="ERROR",
                description=f"è¨­å®ã®ä¿å­ä¸­ã«ã¨ã©ã¼ãçºçãã¾ããã\n```{str(e)}```",
                color=discord.Color.red()
            )
            embed.set_footer(text=interaction.client.embed_footer)
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def stock_notification_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        notification_data = load_stock_notification_data()
        vending_data = load_json(VENDING_DATA_FILE)
        
        choices = []
        for vm_id, notification_info in notification_data.items():
            if notification_info.get("guild_id") == interaction.guild.id:
                vm = vending_data.get(vm_id)
                if vm and vm.get("owner_id") == str(interaction.user.id):
                    vm_name = vm.get("name", "ä¸æãªèªè²©æ©")
                    if current.lower() in vm_name.lower():
                        choices.append(app_commands.Choice(name=vm_name, value=vm_id))
        
        return choices[:25]

    @app_commands.command(name="å¨åº«è¿½å è¨­å®è§£é¤", description="å¨åº«è¿½å éç¥è¨­å®ãè§£é¤ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=stock_notification_autocomplete)
    @app_commands.describe(vending_machine_id="éç¥è¨­å®ãè§£é¤ããèªè²©æ©")
    async def stock_notification_remove(self, interaction, vending_machine_id: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            vending_data = load_json(VENDING_DATA_FILE)
            vm = vending_data.get(vending_machine_id)
            if not vm or vm.get("owner_id") != str(interaction.user.id):
                await interaction.followup.send("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
                return
            
            # éç¥è¨­å®ãåé¤
            notification_data = load_stock_notification_data()
            if vending_machine_id in notification_data:
                del notification_data[vending_machine_id]
                save_stock_notification_data(notification_data)
                
                embed = discord.Embed(
                    title="å¨åº«è¿½å éç¥è¨­å®è§£é¤",
                    description=f"èªè²©æ©ã{vm['name']}ãã®å¨åº«è¿½å éç¥è¨­å®ãè§£é¤ãã¾ããã",
                    color=0x67ACC
                )
                embed.set_footer(text=interaction.client.embed_footer)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("æå®ãããèªè²©æ©ã«éç¥è¨­å®ãè¦ã¤ããã¾ããã", ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="ERROR",
                description=f"è¨­å®ã®åé¤ä¸­ã«ã¨ã©ã¼ãçºçãã¾ããã\n```{str(e)}```",
                color=0x67ACC
            )
            embed.set_footer(text=interaction.client.embed_footer)
            await interaction.followup.send(embed=embed, ephemeral=True)

    # ã¯ã¼ãã³é¢é£ã®ã³ãã³ãï¼èªè²©æ©æå®ï¼
    @app_commands.command(name="èªè²©æ©ã¯ã¼ãã³ä½æ", description="æå®ããèªè²©æ©ç¨ã®ã¯ã¼ãã³ã³ã¼ããä½æãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="ã¯ã¼ãã³ãä½æããèªè²©æ©", coupon_code="ã¯ã¼ãã³ã³ã¼ã", discount="å²å¼éé¡")
    async def vm_create_coupon(self, interaction: discord.Interaction, vending_machine_id: str, coupon_code: str, discount: int):
        try:
            if discount <= 0:
                return await interaction.response.send_message("å²å¼éé¡ã¯1åä»¥ä¸ã§æå®ãã¦ãã ããã", ephemeral=True)
            
            # èªè²©æ©ã®å­å¨ç¢ºèª
            vending_data = load_json(VENDING_DATA_FILE)
            vm = vending_data.get(vending_machine_id)
            if not vm or vm.get("owner_id") != str(interaction.user.id):
                return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
            
            coupon_data = load_coupon_data()
            
            if coupon_code in coupon_data:
                return await interaction.response.send_message("ãã®ã¯ã¼ãã³ã³ã¼ãã¯æ¢ã«å­å¨ãã¾ãã", ephemeral=True)
            
            coupon_data[coupon_code] = {
                "discount": discount,
                "owner_id": str(interaction.user.id),
                "vending_machine_id": vending_machine_id,
                "created_at": str(discord.utils.utcnow())
            }
            
            save_coupon_data(coupon_data)
            
            await interaction.response.send_message(f"èªè²©æ©ã{vm['name']}ãç¨ã®ã¯ã¼ãã³ã³ã¼ãã{coupon_code}ããä½æãã¾ããã\nå²å¼éé¡: {discount}å", ephemeral=True)
        except Exception as e:
            await handle_error(interaction, e)

    @app_commands.command(name="èªè²©æ©ã¯ã¼ãã³åé¤", description="ã¯ã¼ãã³ã³ã¼ããåé¤ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(coupon_code=coupon_autocomplete)
    @app_commands.describe(coupon_code="åé¤ããã¯ã¼ãã³ã³ã¼ã")
    async def vm_delete_coupon(self, interaction: discord.Interaction, coupon_code: str):
        try:
            coupon_data = load_coupon_data()
            
            if coupon_code not in coupon_data:
                return await interaction.response.send_message("æå®ãããã¯ã¼ãã³ã³ã¼ããè¦ã¤ããã¾ããã", ephemeral=True)

            coupon_info = coupon_data[coupon_code]
            if coupon_info.get("owner_id") != str(interaction.user.id):
                return await interaction.response.send_message("ãã®ã¯ã¼ãã³ã³ã¼ããåé¤ããæ¨©éãããã¾ããã", ephemeral=True)

            del coupon_data[coupon_code]
            save_coupon_data(coupon_data)
            
            await interaction.response.send_message(f"ã¯ã¼ãã³ã³ã¼ãã{coupon_code}ããåé¤ãã¾ããã", ephemeral=True)
        except Exception as e:
            await handle_error(interaction, e)

    @app_commands.command(name="èªè²©æ©ã¯ã¼ãã³ä¸è¦§", description="ä½æããã¯ã¼ãã³ã³ã¼ãã®ä¸è¦§ãè¡¨ç¤ºãã¾ã")
    @is_allowed()
    async def vm_list_coupons(self, interaction: discord.Interaction):
        try:
            coupon_data = load_coupon_data()
            vending_data = load_json(VENDING_DATA_FILE)
            user_id_str = str(interaction.user.id)
            
            user_coupons = [
                (coupon_code, coupon_info) for coupon_code, coupon_info in coupon_data.items()
                if coupon_info.get("owner_id") == user_id_str
            ]

            if not user_coupons:
                return await interaction.response.send_message("ä½æããã¯ã¼ãã³ã³ã¼ããããã¾ããã", ephemeral=True)

            embed = discord.Embed(
                title="ã¯ã¼ãã³ã³ã¼ãä¸è¦§",
                color=0x67ACC,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=interaction.client.embed_footer)

            for coupon_code, coupon_info in user_coupons:
                discount = coupon_info.get("discount", 0)
                created_at = coupon_info.get("created_at", "ä¸æ")
                vending_machine_id = coupon_info.get("vending_machine_id", "")
                vm_name = vending_data.get(vending_machine_id, {}).get("name", "ä¸æãªèªè²©æ©")
                
                embed.add_field(
                    name=f"```{coupon_code}```",
                    value=f"å²å¼: {discount}å\nå¯¾è±¡èªè²©æ©: {vm_name}\nä½ææ¥: {created_at[:10]}",
                    inline=True
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await handle_error(interaction, e)

    # ã­ã¼ã«è¨­å®é¢é£ã®ã³ãã³ã
    @app_commands.command(name="èªè²©æ©ã­ã¼ã«è¨­å®", description="è³¼å¥æã«ä»ä¸ããã­ã¼ã«ãè¨­å®ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=vending_machine_autocomplete)
    @app_commands.describe(vending_machine_id="èªè²©æ©", role="è³¼å¥æã«ä»ä¸ããã­ã¼ã«")
    async def vm_set_role(self, interaction: discord.Interaction, vending_machine_id: str, role: discord.Role):
        try:
            vending_data = load_json(VENDING_DATA_FILE)
            vm = vending_data.get(vending_machine_id)
            if not vm or vm.get("owner_id") != str(interaction.user.id):
                return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
            
            role_data = load_role_assignment_data()
            role_data[vending_machine_id] = {
                "role_id": role.id,
                "guild_id": interaction.guild.id
            }
            save_role_assignment_data(role_data)
            
            await interaction.response.send_message(f"èªè²©æ©ã{vm['name']}ãã®è³¼å¥æä»ä¸ã­ã¼ã«ã {role.mention} ã«è¨­å®ãã¾ããã", ephemeral=True)
        except Exception as e:
            await handle_error(interaction, e)

    @app_commands.command(name="èªè²©æ©ã­ã¼ã«è§£é¤", description="è³¼å¥æã®ã­ã¼ã«ä»ä¸è¨­å®ãè§£é¤ãã¾ã")
    @is_allowed()
    @app_commands.autocomplete(vending_machine_id=role_assignment_autocomplete)
    @app_commands.describe(vending_machine_id="ã­ã¼ã«è¨­å®ãè§£é¤ããèªè²©æ©")
    async def vm_remove_role(self, interaction: discord.Interaction, vending_machine_id: str):
        try:
            vending_data = load_json(VENDING_DATA_FILE)
            vm = vending_data.get(vending_machine_id)
            if not vm or vm.get("owner_id") != str(interaction.user.id):
                return await interaction.response.send_message("æå®ãããèªè²©æ©ãè¦ã¤ããã¾ããã", ephemeral=True)
            
            role_data = load_role_assignment_data()
            if vending_machine_id in role_data:
                del role_data[vending_machine_id]
                save_role_assignment_data(role_data)
                
                await interaction.response.send_message(f"èªè²©æ©ã{vm['name']}ãã®ã­ã¼ã«ä»ä¸è¨­å®ãè§£é¤ãã¾ããã", ephemeral=True)
            else:
                await interaction.response.send_message("æå®ãããèªè²©æ©ã«ã­ã¼ã«è¨­å®ãè¦ã¤ããã¾ããã", ephemeral=True)
        except Exception as e:
            await handle_error(interaction, e)

async def setup(bot):
    await bot.add_cog(VendingMachineCog(bot))

