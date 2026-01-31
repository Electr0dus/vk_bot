from vkbottle.bot import BotLabeler, Message, rules


admin_labeler = BotLabeler()
admin_labeler.auto_rules = [rules.FromPeerRule(118331657)] # ID пользователя


@admin_labeler.message(command="halt")
async def halt(_):
    exit(0)

