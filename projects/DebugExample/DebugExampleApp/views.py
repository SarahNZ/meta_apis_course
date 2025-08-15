from django.http import HttpResponse

def display_even_numbers(request):
    response =  ""
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for num in numbers:
        remainder = num % 2
        if remainder == 0:
            response += str(num) + "<br/>"
            
    return HttpResponse(response)
        