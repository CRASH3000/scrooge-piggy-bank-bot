from decimal import Decimal


class VaultBalanceLevelAndRankService:
    @staticmethod
    def get_vault_level_rank_and_image_key_by_balance(balance: Decimal) -> dict:
        if balance <= Decimal("0"):
            return {
                "vault_level_number": 0,
                "vault_rank_name": "Банкрот из Даксбурга",
                "vault_image_key": "IMG_VAULT_EMPTY",
            }

        if Decimal("1") <= balance <= Decimal("9999"):
            return {
                "vault_level_number": 1,
                "vault_rank_name": "Новичок с медным грошом",
                "vault_image_key": "IMG_VAULT_LVL1",
            }

        if Decimal("10000") <= balance <= Decimal("49999"):
            return {
                "vault_level_number": 2,
                "vault_rank_name": "Владелец малого сейфа",
                "vault_image_key": "IMG_VAULT_LVL2",
            }

        if Decimal("50000") <= balance <= Decimal("499999"):
            return {
                "vault_level_number": 3,
                "vault_rank_name": "Золотоискатель Клондайка",
                "vault_image_key": "IMG_VAULT_LVL3",
            }

        return {
            "vault_level_number": 4,
            "vault_rank_name": "Миллионер",
            "vault_image_key": "IMG_VAULT_LVL4",
        }