from django.contrib import admin

from .models import (
    Chat,
    Messaggio,
    AllegatoMessaggio,
    NotificaStaff,
)


class MessaggioInline(admin.TabularInline):
    model = Messaggio
    extra = 0

    readonly_fields = [
        "data_creazione",
    ]


class AllegatoMessaggioInline(admin.TabularInline):
    model = AllegatoMessaggio
    extra = 0

    readonly_fields = [
        "data_caricamento",
    ]


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):

    list_display = [
        "codice",
        "cliente",
        "oggetto",
        "categoria",
        "stato",
        "cliente_ha_risposto",
        "data_apertura",
        "data_modifica",
    ]


    list_filter = [
        "stato",
        "categoria",
        "cliente_ha_risposto",
        "chiusa_da_cliente",
        "data_apertura",
        "data_modifica",
    ]


    search_fields = [
        "codice",
        "cliente__email",
        "oggetto",
        "messaggi__testo",
    ]


    readonly_fields = [
        "codice",
        "data_apertura",
        "data_modifica",
        "data_chiusura",
    ]


    inlines = [
        MessaggioInline,
    ]


@admin.register(Messaggio)
class MessaggioAdmin(admin.ModelAdmin):

    list_display = [
        "chat",
        "mittente_staff",
        "letto",
        "data_creazione",
    ]


    list_filter = [
        "mittente_staff",
        "letto",
        "data_creazione",
    ]


    search_fields = [
        "testo",
        "chat__codice",
        "chat__cliente__email",
    ]


    inlines = [
        AllegatoMessaggioInline,
    ]


@admin.register(AllegatoMessaggio)
class AllegatoMessaggioAdmin(admin.ModelAdmin):

    list_display = [
        "messaggio",
        "nome",
        "data_caricamento",
    ]


@admin.register(NotificaStaff)
class NotificaStaffAdmin(admin.ModelAdmin):

    list_display = [
        "chat",
        "testo",
        "letta",
        "data_creazione",
    ]


    list_filter = [
        "letta",
        "data_creazione",
    ]


    search_fields = [
        "testo",
        "chat__codice",
        "chat__cliente__email",
    ]