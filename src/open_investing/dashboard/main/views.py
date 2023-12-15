from django.shortcuts import render

from rest_framework.response import Response
from adrf.decorators import api_view


@api_view(["GET"])
async def test(request):
    return Response({"message": "This is an async function based view."})


# Create your views here.
