import re


def _validar_cpf_matematico(cpf: str) -> bool:
    
    cpf = re.sub(r'[^0-9]', '', cpf)

    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False

    
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10 or resto == 11:
        resto = 0
    if resto != int(cpf[9]):
        return False

    
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10 or resto == 11:
        resto = 0
    if resto != int(cpf[10]):
        return False

    return True


def validar_cpf_externo(cpf: str) -> bool:
    
    import os
    cpf_limpo = re.sub(r'[^0-9]', '', cpf)

    
    if not _validar_cpf_matematico(cpf_limpo):
        return False

    

    return True  


def formatar_cpf(cpf: str) -> str:
    cpf = re.sub(r'[^0-9]', '', cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}" if len(cpf) == 11 else cpf
