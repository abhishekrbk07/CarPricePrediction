from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect

from .forms import UserForm, TestDriveForm, CompareForm, PriceForm
from .models import Car, TestDrive, Order, Price
from sklearn.model_selection import train_test_split

import pickle
from sklearn.externals import joblib
import json
import numpy as np
import pandas as pd


# Create your views here.
def index(request):
    return render(request, 'web/index.html')


def price(request):
    form = PriceForm(request.POST or None)
    if request.method == 'POST':
        brand = str(request.POST['brand'])
        fuel = str(request.POST['fuel'])
        power = int(request.POST['power'])
        carbon = int(request.POST['carbon'])
        year = int(request.POST['year'])
        mil = float(request.POST['mileage'])

        fis = ((carbon / 45) + (power / 40) ** 1.6)

        df = pd.read_excel(
            "C://Users/Prashant/Desktop/cars/other/car-dealership-system-master/car_dealership/web/data.xlsx")
        data = df[df.price < 400000]
        Y = data.price
        X = pd.read_excel(
            "C://Users/Prashant/Desktop/cars/other/car-dealership-system-master/car_dealership/web/data12.xlsx")

        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=.20, random_state=42)
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import cross_val_score

        gbr = GradientBoostingRegressor(loss='ls', max_depth=6)
        gbr.fit(X_train, Y_train)
        predicted = gbr.predict(X_test)
        residual = Y_test - predicted

        data = {'year_model': year, 'mileage': mil, 'fiscal_power': fis, 'fuel_type': fuel, 'mark': brand}

        enc_input = np.zeros(61)
        enc_input[0] = data['year_model']
        enc_input[1] = data['mileage']
        enc_input[2] = data['fiscal_power']
        marks = df.mark.unique()
        redefinded_user_input = 'mark_' + data['mark']
        mark_column_index = X.columns.tolist().index(redefinded_user_input)
        enc_input[mark_column_index] = 1
        fuel_types = df.fuel_type.unique()
        redefinded_user_input = 'fuel_type_' + data['fuel_type']
        fuelType_column_index = X.columns.tolist().index(redefinded_user_input)
        enc_input[fuelType_column_index] = 1
        a = enc_input
        price_pred = gbr.predict([a])
        p = price_pred[0]

        data1 = {
            'brand': brand,
            'fuel': fuel,
            'power': power,
            'price': p,
            'yrs': year,
            'mil': mil

        }
        html = '''
         
         <body style="background-color:#f2f2f2;">
        <h1 align='center'>Car Information and its Price</h1>
        <table class="table table-bordered">
           <tbody>
            <tr>
                <td>
                Brand Name -
                </td>
                 <td>
                    {brand}
                </td>
                
            </tr>
            <tr>
                <td>
                Fuel Type -
                </td>
                <td>
                {fuel}
                </td>
                
               
            </tr>
            
            <tr>
                <td>
                Power -
                </td>
                <td>
                    {power}
                </td>
                
            </tr>
            
            <tr>
                <td>
                Year Model -
                </td>
                <td>
                    {yrs}
                </td>
                
            </tr>
            <tr>
                <td>
                Mileage -
                </td>
                <td>
                    {mil}
                </td>
                
            </tr>
            <tr>
                <td>
                Price for this Car is-
                </td>
                <td>
                    {price}
                </td>
               
            </tr>
            </tbody>
        </table>
        '''.format(**data1)

        return HttpResponse(html)

    context = {
        'form': form
    }

    return render(request, 'web/price.html', context)


def login_user(request):
    if request.user.is_authenticated:
        return redirect('web:cars')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('web:cars')
            else:
                return render(request, 'web/login.html', {'error_message': 'Your account has not been activated!'})
        else:
            return render(request, 'web/login.html', {'error_message': 'Invalid login'})
    return render(request, 'web/login.html')


def logout_user(request):
    logout(request)
    return redirect('web:index')


def register(request):
    if request.user.is_authenticated:
        return redirect('web:cars')
    uform = UserForm(request.POST or None)
    if uform.is_valid():
        user = uform.save(commit=False)
        username = uform.cleaned_data['username']
        password = uform.cleaned_data['password']
        user.set_password(password)
        user.save()
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('web:dashboard')

    context = {
        "uform": uform,
    }

    return render(request, 'web/register.html', context)


def cars_page(request, pg=1):
    # Each page has 9 requests. That is fixed.
    start = (pg - 1) * 9
    end = start + 9

    car_list = Car.objects.all()[start:end]
    context = {
        'cars': car_list
    }

    return render(request, 'web/cars.html', context)


def car_search(request):
    if request.method == 'GET':
        if request.GET.get('search'):
            search = request.GET.get('search')
        else:
            search = ''
        if request.GET.get('start'):
            start = int(request.GET.get('start'))
        else:
            start = 0
        if request.GET.get('end'):
            end = int(request.GET.get('end'))
        else:
            end = 9

        objs = Car.objects.filter(
            Q(brand__icontains=search) | Q(name__icontains=search)
        )[start:end]
        data = serializers.serialize('json', objs)
        return HttpResponse(data)


def cars(request):
    if request.method == 'GET':
        if request.GET.get('start'):
            start = int(request.GET.get('start'))
        else:
            start = 0
        if request.GET.get('end'):
            end = int(request.GET.get('end'))
        else:
            end = 9
        if request.GET.get('make'):
            make = request.GET.get('make')
            if make == 'all':
                make = ''
        else:
            make = ''
        if request.GET.get('cost_min'):
            cost_min = int(float(request.GET.get('cost_min')))
        else:
            cost_min = 0
        if request.GET.get('cost_max'):
            cost_max = int(float(request.GET.get('cost_max')))
        else:
            cost_max = 999999999
        if request.GET.get('fuel'):
            fuel = request.GET.getlist('fuel')
        else:
            fuel = ['petrol', 'diesel']

        if len(fuel) > 1:
            objs = Car.objects.filter(
                Q(car_make__icontains=make) &
                Q(price__gte=cost_min) &
                Q(price__lte=cost_max) &
                (Q(fuel__icontains=fuel[0]) | Q(fuel__icontains=fuel[1]))
            )[start:end]

        else:
            objs = Car.objects.filter(
                car_make__icontains=make,
                price__gte=cost_min,
                price__lte=cost_max,
                fuel__icontains=fuel[0]
            )[start:end]

    else:
        objs = Car.objects.all()[:9]

    data = serializers.serialize('json', objs)
    return HttpResponse(data)


def car_details(request, cid):
    car = Car.objects.get(pk=cid)
    form = TestDriveForm(initial={'car': car})
    context = {
        'car': car,
        'form': form
    }
    return render(request, 'web/car_details.html', context)


def order_car(request, cid):
    if not request.user.is_authenticated:
        return redirect('web:login')
    user = request.user
    car = Car.objects.get(pk=cid)

    if request.method == 'POST':
        try:
            address = request.POST['address']
            new = Order(
                user=user,
                car=car,
                amount=car.price,
                address=address
            ).save()

            return HttpResponse("Your order has been placed!")
        except Exception as e:
            return HttpResponse("Uh Oh! Something's wrong! Report to the developer with the following error" +
                                e.__str__)
    return HttpResponseForbidden()


def testdrive(request, cid):
    if not request.user.is_authenticated:
        return redirect('web:login')
    user = request.user
    car = Car.objects.get(pk=cid)

    if request.method == 'POST':
        try:
            date = request.POST['date']
            new_date = datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')
            test = TestDrive(
                user=user,
                car=car,
                time=new_date
            ).save()

            return HttpResponse("Your testdrive has been booked!")
        except Exception as e:
            return HttpResponse("Uh Oh! Something's wrong! Report to the developer with the following error" +
                                e.__str__)
    return HttpResponseForbidden()


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('web:login')

    user = request.user
    test = TestDrive.objects.filter(user=user)
    orders = Order.objects.filter(user=user)

    context = {
        'orders': orders,
        'tests': test
    }
    return render(request, 'web/dashboard.html', context)


def compare(request):
    form = CompareForm(request.POST or None)
    if request.method == 'POST':
        car1 = int(request.POST['car1'])
        car2 = int(request.POST['car2'])

        car1 = Car.objects.get(pk=car1)
        car2 = Car.objects.get(pk=car2)

        data = {
            'car1_id': car1.id,
            'car1_name': car1.brand + " " + car1.name,
            'car1_pic': car1.picture.url,
            'car1_price': car1.price,
            'car1_seats': car1.seats,
            'car1_tank_capacity': car1.tank_capacity,
            'car1_transmission': car1.transmission,
            'car1_gears': car1.gears,
            'car1_engine_displacement': car1.engine_displacement,
            'car1_power': car1.power,
            'car1_dimensions': car1.dimensions,
            'car2_id': car2.id,
            'car2_name': car2.brand + " " + car2.name,
            'car2_pic': car2.picture.url,
            'car2_price': car2.price,
            'car2_seats': car2.seats,
            'car2_tank_capacity': car2.tank_capacity,
            'car2_transmission': car2.transmission,
            'car2_gears': car2.gears,
            'car2_engine_displacement': car2.engine_displacement,
            'car2_power': car2.power,
            'car2_dimensions': car2.dimensions,
        }

        html = '''
        <table class="table table-bordered" id="cmpTable">
            <tbody>
            <tr>
                <td>
                </td>
                <td>
                    <a href="car/{car1_id}">{car1_name}</a>
                </td>
                <td>
                    <a href="car/{car2_id}">{car2_name}</a>
                </td>
            </tr>
            <tr>
                <td>
                </td>
                <td>
                    <img class="img-fluid" src="{car1_pic}" alt="">
                </td>
                <td>
                    <img class="img-fluid" src="{car2_pic}" alt="">
                </td>
            </tr>
            <tr>
                <td>
                    Price (in &#8377;)
                </td>
                <td>
                    {car1_price}
                </td>
                <td>
                    {car2_price}
                </td>
            </tr>
            <tr>
                <td>
                    Seating capacity
                </td>
                <td>
                    {car1_seats}
                </td>
                <td>
                    {car2_seats}
                </td>
            </tr>
            <tr>
                <td>
                    Fuel Tank Capacity (litres)
                </td>
                <td>
                    {car1_tank_capacity}
                </td>
                <td>
                    {car2_tank_capacity}
                </td>
            </tr>
            <tr>
                <td>
                    Transmission type
                </td>
                <td>
                    {car1_transmission}
                </td>
                <td>
                    {car2_transmission}
                </td>
            </tr>
            <tr>
                <td>
                    Gears
                </td>
                <td>
                    {car1_gears}
                </td>
                <td>
                    {car2_gears}
                </td>
            </tr>
            <tr>
                <td>
                    Engine displacement (cc)
                </td>
                <td>
                    {car1_engine_displacement}
                </td>
                <td>
                    {car2_engine_displacement}
                </td>
            </tr>
            <tr>
                <td>
                    Maximum power (PS)
                </td>
                <td>
                    {car1_power}
                </td>
                <td>
                    {car2_power}
                </td>
            </tr>
            <tr>
                <td>
                    Dimensions (mm)
                </td>
                <td>
                    {car1_dimensions}
                </td>
                <td>
                    {car2_dimensions}
                </td>
            </tr>
            </tbody>
        </table>
        '''.format(**data)

        return HttpResponse(html)

    context = {
        'form': form
    }

    return render(request, 'web/compare.html', context)
