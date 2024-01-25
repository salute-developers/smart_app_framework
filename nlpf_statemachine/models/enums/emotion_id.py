"""
# Описание списка возможных Эмоций.

Доступные эмоции:

* `igrivost` --- анимация игривости, которую ассистент может испытывать в ответ на дружеские шутки
    и подколки пользователя;
* `udovolstvie` --- анимация удовольствия;
* `podavleniye_gneva` --- анимация подавляемого раздражения на отрицательно окрашенные реплики в адрес ассистента;
* `smushchennaya_ulibka` --- анимация смущения, например, в ответ на похвалу;
* `simpatiya` --- анимация симпатии в ответ на положительно окрашенные реплики;
* `oups` --- анимация неловкости в ответ на лёгкое раздражение или неудобные вопросы пользователя.
    Например, при вопросе вида "Почему такие низкие ставки по вкладам?";
* `laugh` --- анимация смеха над шуткой пользователя;
* `ok_prinyato` --- анимация исполнения запроса;
* `bespokoistvo` --- анимация беспокойства, например, при жалобе пользователя на самочувствие;
* `predvkusheniye` --- анимация возбуждённого ожидания следующей реплики пользователя;
* `vinovatiy` --- анимация вины, например, если в приложении произошла ошибка;
* `zhdu_otvet` --- анимация ожидания реакции от пользователя, например, ответа на заданный вопрос;
* `zadumalsa` --- анимация размышление над репликой пользователя, например, если её не удалось распознать;
* `neznayu` --- анимация отсутствия ответа.
* `nedoumenie` --- анимация сомнения, например, когда не удаётся точно распосзнать реплику.
* `nedovolstvo` --- анимация негативной реакции в ответ на реплику
* `nesoglasie` --- анимация несогласия с пользователем.
* `pechal` --- анимация грусти и тоскливого настроения.
* `radost` --- анимация радости или удовлетворения действиями или репликами пользователя.
* `sochuvstvie` --- анимация сопереживания или выражения участия в проблемах пользователя.
* `strakh` --- анимация испуга.
* `zainteresovannost` --- анимация проявления интереса или любопытства по отношению к действиям
"""

from .smart_enum import SmartEnum


class EmotionId(SmartEnum):
    """
    # Список эмоций.
    """

    igrivost = "igrivost"
    udovolstvie = "udovolstvie"
    podavleniye_gneva = "podavleniye_gneva"
    smushchennaya_ulibka = "smushchennaya_ulibka"
    simpatiya = "simpatiya"
    oups = "oups"
    laugh = "laugh"
    ok_prinyato = "ok_prinyato"
    bespokoistvo = "bespokoistvo"
    predvkusheniye = "predvkusheniye"
    vinovatiy = "vinovatiy"
    zhdu_otvet = "zhdu_otvet"
    zadumalsa = "zadumalsa"
    neznayu = "neznayu"
    nedoumenie = "nedoumenie"
    nedovolstvo = "nedovolstvo"
    nesoglasie = "nesoglasie"
    pechal = "pechal"
    radost = "radost"
    sochuvstvie = "sochuvstvie"
    strakh = "strakh"
    zainteresovannost = "zainteresovannost"
