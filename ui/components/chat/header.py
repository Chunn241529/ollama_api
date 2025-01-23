import flet as ft


def create_header():
    return ft.Row(
        controls=[
            ft.IconButton(icon=ft.icons.MENU, icon_size=20),
            ft.Container(expand=True),
            ft.IconButton(icon=ft.icons.CREATE, icon_size=20),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
